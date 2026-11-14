"""Isolated API cohort: synthetic users, temporary SQLite, no email or LLM calls."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import time
from uuid import uuid4


async def benchmark(users=30, concurrency=10):
    import httpx
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from backend.app.main import app
    from backend.app.database import Base, get_db
    from backend.app import models as m
    with tempfile.TemporaryDirectory(prefix='integrieval-load-') as temporary:
        engine = create_engine('sqlite:///' + str(Path(temporary) / 'test.db'), connect_args={'check_same_thread': False, 'timeout': 30})
        @event.listens_for(engine, 'connect')
        def configure_sqlite(connection, _):
            connection.execute('PRAGMA journal_mode=WAL')
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        tokens = []
        with factory() as db:
            teacher = m.Usuario(nombre='Carga sintética', correo='carga@example.invalid', contrasena='not-a-login', rol='docente')
            db.add(teacher); db.flush()
            course = m.Asignatura(nombre='Prueba aislada', periodo='Piloto', ano=2026, docente_id=teacher.id, parametros={})
            db.add(course); db.flush()
            for number in range(users):
                student = m.Estudiante(nombre=f'Sintético {number}', correo=f'load-{number}@example.invalid', asignatura_id=course.id)
                db.add(student); db.flush()
                work = m.Trabajo(estudiante_id=student.id, markdown='Informe sintético', estado='analizado')
                db.add(work); db.flush()
                evaluation = m.Evaluacion(trabajo_id=work.id, nota=5, pct_ia=0, feedback={}, desglose={})
                db.add(evaluation); db.flush()
                questions = []
                for index in range(2):
                    question = m.Pregunta(evaluacion_id=evaluation.id, texto=f'Pregunta {index}', seleccionada=True,
                        alternativas=[{'id':'A','texto':'Correcta','es_correcta':True},{'id':'B','texto':'Incorrecta','es_correcta':False}])
                    db.add(question); db.flush()
                    questions.append({'id':question.id,'texto':question.texto,'alternativas':question.alternativas})
                test = m.FlashTest(estudiante_id=student.id, token=str(uuid4()), estado='pendiente', vigencia=datetime.now(timezone.utc)+timedelta(hours=1), tiempo_limite_segundos=60)
                db.add(test); db.flush()
                db.add(m.FlashTestState(test_id=test.id, preguntas=questions, indice=0))
                tokens.append(test.token)
            db.commit()
        def dependency():
            with factory() as db:
                yield db
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = dependency
        semaphore = asyncio.Semaphore(concurrency)
        timings, errors = [], []
        started = time.perf_counter()
        try:
            # ASGITransport does not enter app lifespan: real workers and demo seeding stay off.
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://testserver', timeout=30) as client:
                async def request(method, url, **kwargs):
                    before = time.perf_counter()
                    response = await client.request(method, url, **kwargs)
                    timings.append((time.perf_counter()-before)*1000)
                    response.raise_for_status()
                    return response.json()
                async def student(token):
                    async with semaphore:
                        try:
                            root = '/api/flash-test/' + token
                            info = await request('GET', root+'/info')
                            await request('POST', root+'/start')
                            first, second = info['preguntas']
                            await request('POST', root+'/answer', json={'question_id':first['id'],'answer':'A'})
                            resumed = await request('GET', root+'/info')
                            if resumed['pregunta_actual'] != 1:
                                raise ValueError('No recuperó la respuesta guardada')
                            await request('POST', root+'/answer', json={'question_id':second['id'],'answer':'A'})
                            result = await request('POST', root+'/submit', json={'token':token,'respuestas':{}})
                            if result['puntaje'] != 100:
                                raise ValueError('Resultado inesperado')
                        except Exception as error:
                            errors.append(type(error).__name__)
                await asyncio.gather(*(student(token) for token in tokens))
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
            engine.dispose()
        ordered = sorted(timings)
        elapsed = time.perf_counter() - started
        return {'mode':'isolated_synthetic_api','users':users,'concurrency':concurrency,'requests':len(timings),
                'errors':len(errors),'error_types':sorted(set(errors)), 'elapsed_seconds':round(elapsed,2),
                'p50_ms':round(ordered[len(ordered)//2],2) if ordered else None,
                'p95_ms':round(ordered[min(len(ordered)-1,int(len(ordered)*.95))],2) if ordered else None,
                'includes_real_ia':False,'includes_network_or_browser':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--users', type=int, default=30)
    parser.add_argument('--concurrency', type=int, default=10)
    parser.add_argument('--output', default='pilot-results/load.json')
    args = parser.parse_args()
    if not 1 <= args.users <= 200 or not 1 <= args.concurrency <= 30:
        parser.error('Usa de 1 a 200 alumnos y concurrencia de 1 a 30')
    result = asyncio.run(benchmark(args.users, args.concurrency))
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
