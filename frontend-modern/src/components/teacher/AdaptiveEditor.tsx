"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button, Field, Hint, Panel, Select } from "./ui";

type Rule = { base: number; acierto: number; error: number };
type Question = { id: number; text: string; type: string; seccion_origen?: string };

export default function AdaptiveEditor({ evaluationId, questions, selected }: {
  evaluationId: number; questions: Question[]; selected: number[];
}) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(true);
  useEffect(() => {
    let active = true;
    api.getAdaptivePlan(evaluationId).then(data => { if (active) setRules(data); })
      .catch(err => { if (active) setStatus(err.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [evaluationId]);
  const chosen = questions.filter(q => selected.includes(q.id));
  const save = async () => {
    setBusy(true); setStatus("");
    try {
      await api.saveAdaptivePlan(evaluationId, selected, rules);
      setStatus("Selección y repreguntas guardadas.");
    } catch (err: any) { setStatus(err.message); }
    finally { setBusy(false); }
  };
  return <Panel>
    <h3 className="font-bold">Repreguntas adaptativas</h3>
    <Hint>La respuesta a una pregunta de alternativas elige la siguiente. Si acierta se profundiza, si se equivoca se retoma el concepto y si no responde se mantiene la pregunta prevista. El total y el tiempo por pregunta se conservan.</Hint>
    {rules.map((rule, index) => {
      const baseIndex = chosen.findIndex(q => q.id === rule.base);
      const next = baseIndex < 0 ? undefined : chosen[baseIndex + 1];
      const variants = next ? questions.filter(q => !selected.includes(q.id) && q.type === next.type && q.seccion_origen === next.seccion_origen) : [];
      return <div key={index} className="grid gap-2 rounded-control border border-line p-3 md:grid-cols-3">
        {(["base", "acierto", "error"] as const).map(key => <Field key={key} label={{ base: "Pregunta base", acierto: "Si acierta", error: "Si se equivoca" }[key]}>
          <Select value={rule[key] || ""} disabled={busy} onChange={e => {
            const id = Number(e.target.value);
            setRules(previous => previous.map((item, i) => i !== index ? item : key === "base" ? { base: id, acierto: 0, error: 0 } : { ...item, [key]: id }));
          }}>
            <option value="">Selecciona una pregunta</option>
            {(key === "base" ? chosen.slice(0, -1).filter(q => q.type !== "open_ended") : variants).map(q => <option key={q.id} value={q.id}>{q.text}</option>)}
          </Select>
        </Field>)}
        {next && <Hint>Si no responde · {next.text}</Hint>}
        <Button type="button" variant="outline" disabled={busy} onClick={() => setRules(previous => previous.filter((_, i) => i !== index))}>Quitar regla</Button>
      </div>;
    })}
    <div className="flex flex-wrap gap-2">
      <Button variant="outline" disabled={busy || chosen.length < 2 || rules.length >= 7} onClick={() => setRules([...rules, { base: 0, acierto: 0, error: 0 }])}>Agregar repregunta</Button>
      <Button disabled={busy || !chosen.length || rules.some(rule => !rule.base || !rule.acierto || !rule.error)} onClick={save}>Guardar selección y repreguntas</Button>
    </div>
    {status && <p role="status">{status}</p>}
  </Panel>;
}
