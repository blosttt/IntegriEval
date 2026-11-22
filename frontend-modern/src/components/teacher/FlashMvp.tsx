"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Banner, Button, Field, Hint, Input, Panel, Textarea } from "./ui";

type Window = { apertura: string | null; cierre: string | null };
const empty = { apertura: "", cierre: "" };
const local = (value: string | null) => {
  if (!value) return "";
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};

export function FlashWindow({ id, readOnly }: { id: number; readOnly: boolean }) {
  const [draft, setDraft] = useState(empty);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    let active = true;
    api.getFlashWindow(id).then((row: Window) => {
      if (active) setDraft({ apertura: local(row.apertura), cierre: local(row.cierre) });
    }).catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [id]);
  return <Panel className="lg:col-span-3">
    <h2 className="text-lg font-bold">Apertura y cierre del Flash Test</h2>
    <Hint>Las fechas usan la zona de este dispositivo ({Intl.DateTimeFormat().resolvedOptions().timeZone}). Al cierre se entrega el intento en curso con las respuestas guardadas.</Hint>
    <form className="space-y-3" onSubmit={async e => {
      e.preventDefault();
      setError(""); setSaved(false); setBusy(true);
      try {
        const iso = (value: string) => value ? new Date(value).toISOString() : null;
        await api.saveFlashWindow(id, { apertura: iso(draft.apertura), cierre: iso(draft.cierre) });
        setSaved(true);
      } catch (err: any) { setError(err.message); }
      finally { setBusy(false); }
    }}>
      <fieldset disabled={readOnly || busy} className="grid gap-3 sm:grid-cols-2">
        <Field label="Abre el"><Input type="datetime-local" value={draft.apertura} onChange={e => { setSaved(false); setDraft({ ...draft, apertura: e.target.value }); }} /></Field>
        <Field label="Cierra el"><Input type="datetime-local" value={draft.cierre} onChange={e => { setSaved(false); setDraft({ ...draft, cierre: e.target.value }); }} /></Field>
      </fieldset>
      <Hint>Los campos vacíos mantienen el acceso inmediato y la vigencia habitual, según corresponda.</Hint>
      <Button type="submit" disabled={readOnly || busy}>Guardar fechas</Button>
      {saved && <p role="status">Fechas guardadas.</p>}
      {error && <Banner tone="error" role="alert">{error}</Banner>}
    </form>
  </Panel>;
}

type Attempt = { id: number; estudiante_id: number; estudiante: string; estado: string; puntaje: number | null; token: string; retroalimentacion: string | null; nota_cerrada: boolean };
const labels: Record<string, string> = { completado: "Completado", pendiente: "Pendiente", expirado: "Vencido", en_progreso: "En curso" };

export function FlashAttempts({ id, readOnly, onChanged }: { id: number; readOnly: boolean; onChanged: () => void }) {
  const [rows, setRows] = useState<Attempt[]>([]);
  const [selected, setSelected] = useState("");
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  useEffect(() => {
    let active = true;
    api.getFlashAttempts(id).then(data => { if (active) setRows(data); })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [id]);
  const act = async (fn: () => Promise<void>, message: string) => {
    setBusy(true); setError(""); setStatus("");
    try { await fn(); setRows(await api.getFlashAttempts(id)); onChanged(); setStatus(message); }
    catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  };
  const students = new Map(rows.map(row => [row.estudiante_id, row.estudiante]));
  const attempts = rows.filter(row => String(row.estudiante_id) === selected);
  return <Panel>
    <h2 className="text-lg font-bold">Retroalimentación e intentos</h2>
    <Field label="Estudiante"><select className="w-full rounded-control border border-line bg-raised p-2" value={selected} onChange={e => { setSelected(e.target.value); setStatus(""); setError(""); }}>
      <option value="">Selecciona un estudiante</option>
      {[...students].map(([key, name]) => <option key={key} value={key}>{name}</option>)}
    </select></Field>
    {status && <p role="status">{status}</p>}
    {error && <Banner tone="error" role="alert">{error}</Banner>}
    {attempts.map((row, index) => {
      const text = drafts[row.id] ?? row.retroalimentacion ?? "";
      return <section key={row.id} className="space-y-3 rounded-control border border-line p-3">
        <h3 className="font-bold">Intento {index + 1} · {labels[row.estado] ?? row.estado}{row.puntaje !== null ? ` · ${row.puntaje}%` : ""}</h3>
        <a href={`/flash/${encodeURIComponent(row.token)}`} target="_blank" rel="noreferrer" className="text-brand-ink underline">Abrir enlace del intento</a>
        {row.estado === "completado" && <>
          <Field label="Retroalimentación visible para el estudiante"><Textarea value={text} maxLength={5000} disabled={readOnly || busy} onChange={e => setDrafts({ ...drafts, [row.id]: e.target.value })} /></Field>
          <div className="flex flex-wrap gap-2">
            <Button disabled={readOnly || busy || !text.trim()} onClick={() => void act(async () => {
              await api.publishFlashFeedback(row.id, text);
            }, "Retroalimentación publicada en el enlace del estudiante.")}>Publicar retroalimentación</Button>
            {attempts.length === 1 && !row.nota_cerrada && <Button variant="outline" disabled={readOnly || busy} onClick={() => void act(async () => {
              await api.repeatFlashTest(row.id);
            }, "Segundo intento habilitado. El estudiante puede abrirlo desde el resultado del primero.")}>Habilitar segundo intento</Button>}
          </div>
        </>}
      </section>;
    })}
  </Panel>;
}
