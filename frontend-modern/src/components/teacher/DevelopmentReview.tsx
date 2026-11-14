"use client";
import { useEffect, useState, type FormEvent } from "react";
import { request } from "@/lib/api";
import { Banner, Button, Field, Input, Panel, Textarea } from "./ui";

export default function DevelopmentReview({ evaluationId, onSaved }: { evaluationId: number; onSaved: () => void }) {
  const [data, setData] = useState<any>(null);
  const [grades, setGrades] = useState<Record<number, { score: string; comment: string }>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const apply = (result: any) => {
    setData(result);
    setGrades(Object.fromEntries(result.preguntas.map((question: any) => [question.id, { score: question.puntaje == null ? '' : String(question.puntaje), comment: question.comentario || '' }])));
  };
  const load = async () => {
    setBusy(true); setError("");
    try { apply(await request(`/evaluaciones/${evaluationId}/desarrollo`)); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo consultar la revisión'); }
    finally { setBusy(false); }
  };
  useEffect(() => { void load(); }, [evaluationId]);
  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!data?.test_id) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const reviews = data.preguntas.filter((question: any) => !question.sin_respuesta).map((question: any) => {
        const grade = grades[question.id];
        if (!grade || !grade.score.trim() || !Number.isFinite(Number(grade.score)) || !grade.comment.trim()) throw new Error('Indica el puntaje y una justificación para cada respuesta.');
        return { pregunta_id: question.id, puntaje: Number(grade.score), comentario: grade.comment };
      });
      apply(await request(`/flash-tests/${data.test_id}/desarrollo`, 'PUT', { revisiones: reviews }));
      setMessage('Revisión guardada. El puntaje Flash se recalculó con el mismo peso por pregunta.');
      onSaved();
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo guardar la revisión'); }
    finally { setBusy(false); }
  };
  return <Panel className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h3 className="font-bold text-fg">Revisión de desarrollo{data?.estudiante_nombre ? ` · ${data.estudiante_nombre}` : ''}</h3>
      <Button variant="outline" size="toolbar" disabled={busy} onClick={load}>Actualizar respuestas</Button>
    </div>
    {error && <Banner tone="error" role="alert">{error}</Banner>}
    {message && <Banner tone="success" role="status">{message}</Banner>}
    {!data?.preguntas?.length ? <p className="text-sm text-muted">Las respuestas de desarrollo estarán disponibles cuando el estudiante complete el Flash Test.</p>
      : <form className="space-y-5" onSubmit={save}>
        <p className="text-sm text-muted">Cada pregunta vale lo mismo. Las respuestas en blanco reciben cero puntos. El resultado queda pendiente hasta revisar todas las respuestas escritas.</p>
        {data.preguntas.map((question: any) => <fieldset key={question.id} disabled={busy || data.nota_cerrada || question.sin_respuesta} className="space-y-3 rounded-control border border-line p-4">
          <legend className="px-2 font-semibold text-fg">{question.texto}</legend>
          <p className="whitespace-pre-wrap text-fg">{question.respuesta || 'Sin respuesta · 0 puntos'}</p>
          <details className="text-sm text-muted"><summary className="cursor-pointer">Pauta privada del docente</summary>
            <p className="mt-2 whitespace-pre-wrap">{question.criterios_evaluacion || 'Sin criterios registrados'}</p>
            {question.respuesta_referencia && <p className="mt-2 whitespace-pre-wrap">Referencia: {question.respuesta_referencia}</p>}
          </details>
          {!question.sin_respuesta && <>
            <Field label="Puntaje de la respuesta (0 a 100)"><Input type="number" min={0} max={100} step="0.1" required value={grades[question.id]?.score || ''} onChange={e => setGrades(current => ({ ...current, [question.id]: { ...current[question.id], score: e.target.value } }))} /></Field>
            <Field label="Justificación de la revisión"><Textarea required maxLength={2000} value={grades[question.id]?.comment || ''} onChange={e => setGrades(current => ({ ...current, [question.id]: { ...current[question.id], comment: e.target.value } }))} /></Field>
          </>}
        </fieldset>)}
        {data.nota_cerrada ? <p className="text-sm text-muted">La calificación está cerrada; la revisión es de solo lectura.</p>
          : data.preguntas.some((question: any) => !question.sin_respuesta) && <Button variant="primary" size="classic" type="submit" disabled={busy}>{busy ? 'Guardando…' : 'Guardar revisión de desarrollo'}</Button>}
      </form>}
  </Panel>;
}
