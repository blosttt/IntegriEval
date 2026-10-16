"""Non-destructive SQLite upgrade for multiple evaluations per course."""
from sqlalchemy import inspect


def upgrade_activities(engine):
    if engine.dialect.name != 'sqlite':
        return
    columns = {c['name'] for c in inspect(engine).get_columns('trabajos')}
    if 'actividad_id' in columns:
        return
    import sqlite3
    from datetime import datetime
    path = engine.url.database
    if path and path != ':memory:':
        with sqlite3.connect(path) as source, sqlite3.connect(path + '.before-activities-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.bak') as backup:
            source.backup(backup)
    with engine.connect() as connection:
        connection.exec_driver_sql('PRAGMA foreign_keys=OFF')
        connection.commit()
        with connection.begin():
            connection.exec_driver_sql('CREATE TABLE trabajos_upgrade (id INTEGER PRIMARY KEY, estudiante_id INTEGER NOT NULL REFERENCES estudiantes(id), actividad_id INTEGER REFERENCES actividades(id), pdf_path VARCHAR(500), markdown TEXT, estado VARCHAR(50), fecha_entrega DATETIME, CONSTRAINT uq_trabajo_actividad UNIQUE(estudiante_id, actividad_id))')
            connection.exec_driver_sql('INSERT INTO trabajos_upgrade (id,estudiante_id,pdf_path,markdown,estado,fecha_entrega) SELECT id,estudiante_id,pdf_path,markdown,estado,fecha_entrega FROM trabajos')
            connection.exec_driver_sql('DROP TABLE trabajos')
            connection.exec_driver_sql('ALTER TABLE trabajos_upgrade RENAME TO trabajos')
            for table in ('flash_tests','citas'):
                connection.exec_driver_sql(f'ALTER TABLE {table} ADD COLUMN actividad_id INTEGER REFERENCES actividades(id)')
        connection.exec_driver_sql('PRAGMA foreign_keys=ON')
