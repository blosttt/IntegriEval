"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import AddQuestionModal from "../AddQuestionModal";
import { Banner, Button, Field, Hint, Panel, Select } from "../ui";

type AssignedQuestion = { texto: string; tipo: string; pool_general: boolean };
type Assignment = {
  estudiante_id: number;
  estudiante: string;
  seleccion: AssignedQuestion[];
  intentos: { id: number; estado: string; preguntas: AssignedQuestion[] | null }[];
};

const statuses: Record<string, string> = {
  pendiente: "Despachado · pendiente",
  en_progreso: "En curso",
  completado: "Completado",
  expirado: "Vencido",
};

function AssignedQuestions({ questions }: { questions: AssignedQuestion[] | null }) {
  if (!questions) return <Hint>Este intento histórico no tiene una copia de las preguntas.</Hint>;
  return <ol className="list-decimal space-y-1 pl-5">
    {questions.map((question, index) => <li key={index}>
      {question.texto}
      <span className="ml-2 text-xs text-muted">
        {question.pool_general ? "Pool general" : "Pool individual"}
        {question.tipo === "desarrollo" && " · Desarrollo"}
      </span>
    </li>)}
  </ol>;
}

export default function GeneralPool({ evaluationId, count, readOnly, revision, onDrawn, onDrawing }: {
  evaluationId: number;
  count: number;
  readOnly: boolean;
  revision: number;
  onDrawn: () => Promise<void>;
  onDrawing: (drawing: boolean) => void;
}) {
  const [criteriaNames, setCriteriaNames] = useState<string[]>([]);
  const [questions, setQuestions] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [editor, setEditor] = useState<{ question?: any } | null>(null);
  const [source, setSource] = useState("mixto");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<{ asignados: number; ya_despachados: number; omitidos: { estudiante: string; motivo: string }[] } | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([api.getGeneralQuestions(evaluationId), api.getAssessmentSetup(evaluationId)])
      .then(([data, setup]) => {
        if (active) {
          setQuestions(data);
          setCriteriaNames(setup?.criterios.map((row: { nombre: string }) => row.nombre) ?? []);
        }
      })
      .catch(err => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [evaluationId]);

  useEffect(() => {
    let active = true;
    api.getQuestionAssignments(evaluationId).then(data => { if (active) setAssignments(data); })
      .catch(err => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [evaluationId, revision]);

  const draw = async () => {
    if (!window.confirm("¿Sortear las preguntas y reemplazar las selecciones de los estudiantes que aún no tienen un Flash Test despachado?")) return;
    setBusy(true);
    onDrawing(true);
    setError("");
    setSummary(null);
    try {
      setSummary(await api.drawGeneralQuestions(evaluationId, source));
      const [data] = await Promise.all([api.getQuestionAssignments(evaluationId), onDrawn()]);
      setAssignments(data);
    } catch (err: any) { setError(err.message); }
    finally { setBusy(false); onDrawing(false); }
  };

  const remove = async (id: number) => {
    if (!window.confirm("¿Eliminar la pregunta del pool general? Las copias ya asignadas se conservan.")) return;
    setBusy(true);
    setError("");
    try {
      await api.deleteGeneralQuestion(evaluationId, id);
      setQuestions(previous => previous.filter(q => q.id !== id));
    } catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  };

  return <>
    <Panel>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-fg">Pool general de la evaluación</h2>
          <Hint>Guarda preguntas propias una vez y reutilízalas en los Flash Tests de esta evaluación.</Hint>
        </div>
        <Button variant="outline" disabled={readOnly || busy} onClick={() => setEditor({})}>Agregar pregunta al pool general</Button>
      </div>
      {questions.length === 0 && <Hint>Todavía no hay preguntas propias en este pool.</Hint>}
      {questions.length > 0 && <details>
        <summary className="cursor-pointer text-sm font-semibold text-fg">Ver preguntas del pool general ({questions.length})</summary>
        <ul className="mt-3 space-y-2">
          {questions.map(q => <li key={q.id} className="flex flex-wrap items-center justify-between gap-2 rounded-control border border-line p-3">
            <span className="text-sm text-fg">{q.text} <span className="text-xs text-muted">· {q.type === "open_ended" ? "Desarrollo" : q.type === "true_false" ? "Verdadero / Falso" : "Alternativas"}</span></span>
            <div className="flex gap-2">
              <Button variant="outline" size="toolbar" disabled={readOnly || busy} onClick={() => setEditor({ question: q })}>Editar</Button>
              <Button variant="muted" size="toolbar" disabled={readOnly || busy} onClick={() => remove(q.id)}>Eliminar</Button>
            </div>
          </li>)}
        </ul>
      </details>}
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Origen de las preguntas">
          <Select value={source} disabled={readOnly || busy} onChange={e => setSource(e.target.value)}>
            <option value="mixto">Pool general + preguntas individuales</option>
            <option value="general">Solo pool general</option>
            <option value="individual">Solo preguntas individuales</option>
          </Select>
        </Field>
        <Button disabled={readOnly || busy} onClick={draw}>{busy ? "Procesando…" : "Sortear para los estudiantes"}</Button>
      </div>
      <Hint>Prepara {count} preguntas por estudiante con informe analizado y sin test despachado. Revisa las selecciones antes de aprobar el envío.</Hint>
      {error && <Banner tone="error" role="alert">{error}</Banner>}
      {summary && <div role="status" className="text-sm text-fg">
        <p>Selecciones preparadas: {summary.asignados}. Con test previo: {summary.ya_despachados}.</p>
        {summary.omitidos.length > 0 && <details className="mt-2">
          <summary className="cursor-pointer">Ver estudiantes omitidos ({summary.omitidos.length})</summary>
          <ul className="mt-1 list-disc pl-5">{summary.omitidos.map(item => <li key={item.estudiante + item.motivo}>{item.estudiante} · {item.motivo}</li>)}</ul>
        </details>}
      </div>}
    </Panel>

    <Panel>
      <h2 className="text-lg font-bold text-fg">Preguntas por estudiante</h2>
      <Hint>Consulta la selección antes del envío y las preguntas exactas que recibió cada estudiante después del despacho.</Hint>
      {assignments.length === 0 && <Hint>Aún no hay selecciones ni tests despachados.</Hint>}
      {assignments.map(item => <details key={item.estudiante_id} className="rounded-control border border-line p-3 text-sm text-fg">
        <summary className="cursor-pointer font-semibold">{item.estudiante} · {item.intentos.length ? statuses[item.intentos[0].estado] || item.intentos[0].estado : "Selección por aprobar"}</summary>
        <div className="mt-2 space-y-3">
          {item.seleccion.length > 0 && <AssignedQuestions questions={item.seleccion} />}
          {item.intentos.map((attempt, index) => <section key={attempt.id}>
            {item.intentos.length > 1 && <p className="mb-1 font-semibold">Intento {item.intentos.length - index} · {statuses[attempt.estado] || attempt.estado}</p>}
            <AssignedQuestions questions={attempt.preguntas} />
          </section>)}
        </div>
      </details>)}
    </Panel>
    {editor && <AddQuestionModal criteriaNames={criteriaNames} question={editor.question} onClose={() => setEditor(null)} onSave={async data => {
      await api.saveGeneralQuestion(evaluationId, data, editor.question?.id);
      setQuestions(await api.getGeneralQuestions(evaluationId));
    }} />}
  </>;
}
