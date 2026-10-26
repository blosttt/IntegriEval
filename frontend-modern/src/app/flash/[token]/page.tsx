"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import { Banner, Button, Panel, shellClasses } from "@/components/ui";

type Question = { id: number; texto: string; alternativas: { id: string; texto: string }[] };
type Session = {
  estado: string; estudiante_nombre: string; asignatura_nombre: string;
  asignatura_periodo: string; num_preguntas: number; pregunta_actual: number;
  tiempo_segundos: number; tiempo_restante_segundos: number; preguntas: Question[];
};
type Result = { porcentaje_logro: number; respuestas_correctas: number; tiempo_transcurrido: number };
type Action = "info" | "start" | "answer";

export default function FlashPage() {
  const { token } = useParams<{ token: string }>();
  return <FlashSession key={token} token={token} />;
}

function FlashSession({ token }: { token: string }) {
  const [session, setSession] = useState<Session | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [unavailable, setUnavailable] = useState(false);
  const [busy, setBusy] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const run = useRef<(action: Action, body?: object) => void>(() => {});

  useEffect(() => {
    const controller = new AbortController();
    let running = false, stopped = false, terminal = false;
    let queued: { action: Action; body?: object } | null = null;
    let deadline: number | null = null;
    const request = async (action: string, body?: object) => {
      const response = await fetch(`/api/flash-test/${encodeURIComponent(token)}/${action}`, {
        method: body ? "POST" : "GET", cache: "no-store",
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        if ([404, 410].includes(response.status)) { terminal = true; setUnavailable(true); }
        throw new Error(typeof data.detail === "string" ? data.detail : "No se pudo conectar. Vuelve a intentar.");
      }
      return data;
    };
    const refresh = async (action: Action = "info", body?: object) => {
      if (stopped || terminal) return;
      if (running) {
        if (action !== "info") { queued = { action, body }; setBusy(true); }
        return;
      }
      running = true;
      if (action !== "info") setBusy(true);
      try {
        const data: Session = await request(action, body);
        if (stopped) return;
        setSession(data);
        deadline = data.estado === "en_progreso" ? performance.now() + data.tiempo_restante_segundos * 1000 : null;
        setSeconds(data.tiempo_restante_segundos);
        if (data.estado === "completado") {
          // The server already scored the persisted answers. Retrieve its idempotent result.
          const score: Result = await request("submit", { token, respuestas: {}, tiempo_transcurrido: 0 });
          if (!stopped) { setResult(score); terminal = true; }
        }
        if (!stopped) setError("");
      } catch (e) {
        if (!stopped) setError(e instanceof Error && !["TimeoutError", "AbortError"].includes(e.name)
          ? e.message : "La conexión tardó demasiado. Reintentaremos sin reiniciar tu sesión.");
      } finally {
        running = false;
        if (!stopped) setBusy(false);
        const next = queued;
        queued = null;
        if (next && !stopped && !terminal) void refresh(next.action, next.body);
      }
    };
    run.current = (action, body) => { void refresh(action, body); };
    void refresh();
    // Same-origin HTTP polling resumes persisted progress after disconnection.
    const poll = setInterval(() => { void refresh(); }, 1500);
    const timer = setInterval(() => {
      if (!stopped && deadline !== null && !terminal)
        setSeconds(Math.max(0, Math.ceil((deadline - performance.now()) / 1000)));
    }, 250);
    return () => { stopped = true; controller.abort(); clearInterval(poll); clearInterval(timer); run.current = () => {}; };
  }, [token]);

  useEffect(() => { heading.current?.focus(); }, [session?.pregunta_actual, session?.estado]);
  const question = session?.preguntas[session.pregunta_actual];
  const active = session?.estado === "en_progreso";
  return <div className={shellClasses}>
    <Navbar />
    <main className="mx-auto w-full max-w-3xl space-y-5 px-5 py-10 text-fg">
      <div><p className="text-sm font-semibold text-brand-ink">IntegryEval · Flash Test</p>
        <h1 className="mt-2 text-3xl font-bold">Verificación de tu informe</h1>
        {session && <p className="mt-2 text-muted">{session.estudiante_nombre} · {session.asignatura_nombre} · {session.asignatura_periodo}</p>}
      </div>
      {error && <Banner tone="error" role="alert"><p style={{ color: "var(--ie-text)" }}>{error}</p>
        {active && <p style={{ color: "var(--ie-text)" }}>El tiempo sigue corriendo en el servidor. Al reconectar se recuperará el avance guardado.</p>}
        {!unavailable && <Button className="mt-3" onClick={() => run.current("info")}>Reintentar conexión</Button>}
      </Banner>}
      {unavailable ? <Panel><h2 className="text-xl font-bold">Enlace no disponible</h2><p>Contacta a tu profesor para revisar la vigencia de tu Flash Test.</p></Panel>
        : result ? <Panel className="text-center" aria-live="polite">
          <h2 className="text-2xl font-bold">Flash Test completado</h2>
          <p className="text-5xl font-bold text-brand-ink">{result.porcentaje_logro}%</p>
          <p>{result.respuestas_correctas} de {session?.num_preguntas} respuestas correctas · {result.tiempo_transcurrido} segundos</p>
          <p className="text-muted">Tus respuestas quedaron guardadas. Tu profesor revisará el resultado junto con tu informe y te avisará si corresponde una revisión.</p>
        </Panel>
        : !session ? <Panel role="status">{error ? "No pudimos cargar la evaluación." : "Cargando tu Flash Test…"}</Panel>
        : session.estado === "pendiente" ? <Panel>
          <h2 className="text-xl font-bold">Antes de comenzar</h2>
          <p>{session.num_preguntas} preguntas · {session.tiempo_segundos} segundos por pregunta.</p>
          <ul className="list-disc space-y-2 pl-5 text-muted">
            <li>Las preguntas se basan en tu informe. Al elegir una alternativa se guarda y avanzas.</li>
            <li>No puedes volver a preguntas anteriores. El tiempo se controla en el servidor.</li>
            <li>Si recargas la página, recuperarás el avance; el cronómetro no se detiene.</li>
            <li>Si pierdes conexión, reconecta cuanto antes. Solo se califican respuestas guardadas.</li>
          </ul>
          <Button disabled={busy} onClick={() => run.current("start", {})}>{busy ? "Iniciando…" : "Comenzar Flash Test"}</Button>
        </Panel>
        : active && question ? <Panel>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-semibold">Pregunta {session.pregunta_actual + 1} de {session.num_preguntas}</p>
            <span role="timer" aria-label="Segundos restantes" className={seconds <= 10 ? "font-bold text-red-400" : "font-bold text-brand-ink"}>{seconds} s</span>
          </div>
          <progress className="h-2 w-full accent-blue-500" aria-label="Avance del test" value={session.pregunta_actual} max={session.num_preguntas} />
          <h2 ref={heading} tabIndex={-1} className="text-xl font-semibold outline-none">{question.texto}</h2>
          <div className="grid gap-3">{question.alternativas.map((alternative) => <button
            key={alternative.id} type="button" disabled={busy || seconds === 0}
            className="flex items-start gap-3 rounded-control border border-line bg-raised p-4 text-left hover:border-brand focus-visible:outline-2 focus-visible:outline-brand disabled:cursor-wait disabled:opacity-60"
            onClick={() => run.current("answer", { question_id: question.id, answer: alternative.id })}
          ><span className="font-bold text-brand-ink">{alternative.id}</span><span>{alternative.texto}</span></button>)}</div>
          <p className="text-sm text-muted" role="status">{busy ? "Guardando respuesta…" : seconds === 0 ? "Sincronizando la siguiente pregunta…" : "Al seleccionar una alternativa, avanzas a la siguiente pregunta."}</p>
        </Panel>
        : <Panel role="status">Confirmando el resultado guardado…</Panel>}
    </main>
  </div>;
}
