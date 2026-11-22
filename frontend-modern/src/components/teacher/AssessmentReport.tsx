"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Banner, Button, Field, Hint, Input, Panel, Select, Textarea } from "./ui";

type Finding = { criterio: string; puntaje: number | null; observacion: string; evidencia: string; fuente: string; pregunta: number | null; entrevista: string };
type Review = { criterios: Finding[]; puntaje: number | null; cobertura: number };
type Comparison = { error_medio: number | null; criterios_comparables: number };
type Report = {
  desempeno: { informe: string | null; flash: number | null };
  calibracion: (Review & { antes: Comparison; despues: Comparison }) | null;
  rubrica: { version: number; criterios: { nombre: string; peso: number; descripcion: string }[] } | null;
  informe: string | null;
  registro: { orden: number; pregunta: string; respuesta: string; respuesta_esperada?: string; pauta?: string; rama?: string; depende_de?: number }[];
  docente: Review | null; ia: Review | null; ia_generada: boolean;
  contraste: { acuerdo: boolean; comentario: string } | null;
};

function Summary({ title, review }: { title: string; review: Review }) {
  return <section className="space-y-2 rounded-control border border-line p-3">
    <h4 className="font-bold">{title}</h4>
    <p>{review.puntaje === null ? "Puntaje global pendiente de evidencia" : `${review.puntaje}% global`} · Cobertura {review.cobertura}%</p>
    {review.criterios.map(item => <div key={item.criterio} className="border-t border-line pt-2">
      <p className="font-semibold">{item.criterio} · {item.puntaje === null ? "Sin evidencia" : `${item.puntaje}% · ${item.puntaje >= 75 ? "Fortaleza" : item.puntaje < 60 ? "Debilidad" : "En desarrollo"}`}</p>
      <p>{item.observacion}</p>
      {item.evidencia && <blockquote className="my-1 border-l-2 border-line pl-2">«{item.evidencia}» · {item.fuente === "informe" ? "Informe" : `Respuesta ${item.pregunta}`}</blockquote>}
      {item.entrevista && <p className="text-muted">Entrevista · {item.entrevista}</p>}
    </div>)}
  </section>;
}

export default function AssessmentReport({ testId }: { testId: number }) {
  const [report, setReport] = useState<Report>();
  const [draft, setDraft] = useState<Finding[]>([]);
  const [verdict, setVerdict] = useState({ acuerdo: true, comentario: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const reload = async () => setReport(await api.getAssessmentReport(testId));
  useEffect(() => {
    let active = true;
    api.getAssessmentReport(testId).then((data: Report) => {
      if (!active) return;
      setReport(data);
      setDraft(data.rubrica?.criterios.map(row => ({
        criterio: row.nombre, puntaje: null, observacion: "", evidencia: "", fuente: "sin_evidencia", pregunta: null, entrevista: "",
      })) ?? []);
      if (data.contraste) setVerdict(data.contraste);
    }).catch(err => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [testId]);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true); setError("");
    try { await fn(); await reload(); } catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  };
  const change = (index: number, update: Partial<Finding>) =>
    setDraft(previous => previous.map((row, i) => i === index ? { ...row, ...update } : row));

  return <div className="space-y-4 text-sm">
    {error && <Banner tone="error" role="alert">{error}</Banner>}
    {!report && !error && <Hint>Cargando registro…</Hint>}
    {report && <>
      <div className="grid gap-3 sm:grid-cols-3">
        <section className="rounded-control border border-line border-t-4 border-t-sky-500 p-3"><h4 className="font-bold">Informe del proyecto</h4><p>{report.desempeno.informe ?? "Sin puntaje"}</p></section>
        <section className="rounded-control border border-line border-t-4 border-t-violet-500 p-3"><h4 className="font-bold">Flash Test</h4><p>{report.desempeno.flash === null ? "Pendiente de corrección" : `${report.desempeno.flash}%`}</p></section>
        <section className="rounded-control border border-line border-t-4 border-t-emerald-500 p-3"><h4 className="font-bold">Revisión docente</h4><p>{report.docente ? report.docente.puntaje === null ? "Revisión registrada · evidencia parcial" : `${report.docente.puntaje}%` : "Por registrar"}</p></section>
      </div>
      <Button variant="outline" disabled={busy} onClick={() => void act(() => api.downloadAssessment(testId))}>Descargar informe individual (PDF)</Button>
      <details><summary className="cursor-pointer font-semibold">Preguntas y respuestas exactas</summary>
        <ol className="mt-2 list-decimal space-y-3 pl-5">{report.registro.map(row => <li key={row.orden}>
          <strong>{row.pregunta}</strong>
          <p className="whitespace-pre-wrap">{row.respuesta || "Sin respuesta"}</p>
          {row.respuesta_esperada && <Hint>Respuesta de referencia · {row.respuesta_esperada}</Hint>}
          {row.rama && <Hint>Repregunta tras la pregunta {row.depende_de} · {{ acierto: "acierto (versión anterior)", error: "ayuda tras error", sin_respuesta: "pregunta en blanco" }[row.rama]}</Hint>}
          {row.pauta && <Hint>Pauta · {row.pauta}</Hint>}
        </li>)}</ol>
      </details>
      {report.informe && <details><summary className="cursor-pointer font-semibold">Texto extraído del informe</summary>
        <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-control border border-line p-3">{report.informe}</pre>
      </details>}
      {!report.rubrica ? <Hint>Este informe se analizó antes de registrar una rúbrica para su evaluación.</Hint> : <>
        <p className="font-semibold">Rúbrica aplicada · versión {report.rubrica.version}</p>
        <Button type="button" disabled={busy || report.ia_generada} onClick={() => act(() => api.generateAssessmentReport(testId))}>
          {report.ia_generada ? "Reporte de IA generado" : busy ? "Procesando…" : "Generar reporte con Ollama"}
        </Button>
        {!report.docente && <form className="space-y-3" onSubmit={e => {
          e.preventDefault();
          if (window.confirm("¿Guardar la revisión independiente y habilitar el contraste con la IA?")) {
            void act(() => api.saveAssessmentReview(testId, { criterios: draft }));
          }
        }}>
          <h4 className="font-bold">Evaluación independiente del docente</h4>
          <Hint>Guarda tu evaluación para abrir el reporte de IA y comparar los resultados.</Hint>
          {draft.map((row, index) => <fieldset disabled={busy} key={row.criterio} className="space-y-2 rounded-control border border-line p-3">
            <legend className="font-semibold">{row.criterio} ({report.rubrica!.criterios[index].peso}%)</legend>
            <Hint>{report.rubrica!.criterios[index].descripcion}</Hint>
            <Field label="Fuente de evidencia"><Select value={row.fuente} onChange={e => change(index, { fuente: e.target.value, pregunta: null })}>
              <option value="sin_evidencia">Sin evidencia</option><option value="informe">Informe</option><option value="respuesta">Respuesta del Flash Test</option>
            </Select></Field>
            {row.fuente === "respuesta" && <Field label="Pregunta"><Select required value={row.pregunta ?? ""} onChange={e => change(index, { pregunta: Number(e.target.value) || null })}>
              <option value="">Selecciona una pregunta</option>
              {report.registro.map(item => <option key={item.orden} value={item.orden}>{item.orden}. {item.pregunta}</option>)}
            </Select></Field>}
            {row.fuente !== "sin_evidencia" && <>
              <Field label="Puntaje (0 a 100)"><Input required type="number" min={0} max={100} step="any" value={row.puntaje ?? ""} onChange={e => change(index, { puntaje: e.target.value === "" ? null : Number(e.target.value) })} /></Field>
              <Field label="Cita literal de la evidencia"><Textarea required maxLength={1200} value={row.evidencia} onChange={e => change(index, { evidencia: e.target.value })} /></Field>
            </>}
            <Field label="Observación"><Textarea required maxLength={1200} value={row.observacion} onChange={e => change(index, { observacion: e.target.value })} /></Field>
            <Field label="Qué profundizar en la entrevista"><Textarea maxLength={600} value={row.entrevista} onChange={e => change(index, { entrevista: e.target.value })} /></Field>
          </fieldset>)}
          <Button type="submit" disabled={busy}>Guardar evaluación docente</Button>
        </form>}
        {report.docente && <div className="grid gap-3 md:grid-cols-2">
          <Summary title="Evaluación docente" review={report.docente} />
          {report.ia && <Summary title="Evaluación de la IA" review={report.ia} />}
        </div>}
        {report.docente && report.ia && <form className="space-y-2" onSubmit={e => { e.preventDefault(); void act(() => api.saveAssessmentVerdict(testId, verdict)); }}>
          {report.docente.puntaje !== null && report.ia.puntaje !== null && <p>Diferencia absoluta · {Math.abs(report.docente.puntaje - report.ia.puntaje).toFixed(1)} puntos</p>}
          <Field label="Veredicto docente"><Select value={verdict.acuerdo ? "si" : "no"} onChange={e => setVerdict({ ...verdict, acuerdo: e.target.value === "si" })}>
            <option value="si">De acuerdo</option><option value="no">En desacuerdo</option>
          </Select></Field>
          <Field label="Motivo del contraste"><Textarea required maxLength={3000} value={verdict.comentario} onChange={e => setVerdict({ ...verdict, comentario: e.target.value })} /></Field>
          <Button type="submit" disabled={busy}>Guardar contraste</Button>
          {report.contraste && <Hint>Veredicto guardado · {report.contraste.acuerdo ? "De acuerdo" : "En desacuerdo"}</Hint>}
        </form>}
        {report.contraste && <Button variant="outline" disabled={busy} onClick={() => void act(() => api.calibrateAssessment(testId))}>
          Reevaluar con la retroalimentación docente
        </Button>}
        {report.calibracion && <div className="space-y-2">
          <p>Error medio frente al docente · Antes {report.calibracion.antes.error_medio ?? "sin datos"} / Después {report.calibracion.despues.error_medio ?? "sin datos"} puntos</p>
          <p>Criterios comparables · Antes {report.calibracion.antes.criterios_comparables} / Después {report.calibracion.despues.criterios_comparables}</p>
          <Summary title="Reevaluación con retroalimentación docente" review={report.calibracion} />
        </div>}
      </>}
    </>}
  </div>;
}

export function AssessmentReports({ reports }: { reports: { id: number; flash_test_id: number; flash_completed: boolean; student_name: string }[] }) {
  const [selected, setSelected] = useState(0);
  const completed = reports.filter(item => item.flash_completed && item.flash_test_id);
  return <Panel>
    <h2 className="text-lg font-bold">Reporte por rúbrica y calibración</h2>
    {completed.length ? <Field label="Flash Test completado"><Select value={completed.some(r => r.flash_test_id === selected) ? selected : ""} onChange={e => setSelected(Number(e.target.value))}>
      <option value="">Selecciona un estudiante</option>
      {completed.map(item => <option key={item.id} value={item.flash_test_id}>{item.student_name}</option>)}
    </Select></Field> : <Hint>Aún no hay Flash Tests completados en esta evaluación.</Hint>}
    {completed.some(item => item.flash_test_id === selected) && <AssessmentReport key={selected} testId={selected} />}
  </Panel>;
}
