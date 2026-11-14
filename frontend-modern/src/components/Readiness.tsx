"use client";

import { useState } from "react";
import Dialog from "./Dialog";
import { request } from "@/lib/api";
import { Banner, Button, Panel } from "./ui";

type Status = {
  environment: string;
  checks: { id: string; label: string; ok: boolean }[];
  backup: { filename: string | null; state: string; missing_documents: number | null };
  manual_checks: string[];
};

export default function Readiness() {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const load = async () => setStatus(await request('/admin/preparacion'));
  const show = async () => {
    setOpen(true); setBusy(true); setError(""); setMessage("");
    try { await load(); } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo consultar'); }
    finally { setBusy(false); }
  };
  const backup = async () => {
    setBusy(true); setError(""); setMessage("");
    try {
      const result = await request('/admin/respaldos', 'POST');
      setMessage(`Respaldo creado: ${result.filename}. Documentos guardados: ${result.documents}. Documentos faltantes: ${result.missing_documents}.`);
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo respaldar'); }
    finally { setBusy(false); }
  };
  return <>
    <Button variant="surface" size="classic" onClick={show}>Preparación y respaldos</Button>
    {open && <Dialog wide title="Preparación para uso real" onClose={() => { if (!busy) setOpen(false); }}>
      <div className="space-y-5 p-6">
      {error && <Banner tone="error" role="alert">{error}</Banner>}
      {message && <Banner tone="success" role="status">{message}</Banner>}
      {status && <div className="space-y-5">
        <p className="text-muted">Entorno: {status.environment}. Estos controles verifican configuración; no sustituyen un piloto.</p>
        <Panel><ul className="space-y-3">{status.checks.map(check => <li key={check.id} className="flex justify-between gap-4">
          <span>{check.label}</span><strong className="shrink-0">{check.ok ? 'Listo' : 'Pendiente'}</strong>
        </li>)}</ul></Panel>
        <Panel><h3 className="font-bold">Último respaldo</h3><p className="break-all">{status.backup.filename || 'Todavía no hay respaldos'}</p>
          <p>Estado: {status.backup.state}. Documentos faltantes: {status.backup.missing_documents ?? '—'}.</p>
          <p className="text-sm text-muted">Incluye base y documentos referenciados; no incluye contraseñas del servidor ni modelos de IA. La restauración se realiza desde terminal, en una carpeta nueva.</p>
          <Button variant="primary" size="classic" onClick={backup} disabled={busy}>{busy ? 'Procesando…' : 'Crear respaldo ahora'}</Button>
        </Panel>
        <div><h3 className="font-bold">Verificaciones con personas y dispositivos</h3><ul className="mt-3 list-disc space-y-2 pl-5 text-muted">{status.manual_checks.map(item => <li key={item}>{item}</li>)}</ul></div>
      </div>}
      {!status && <p role="status">{busy ? 'Comprobando preparación…' : 'No se pudo cargar el estado.'}</p>}
      </div>
    </Dialog>}
  </>;
}
