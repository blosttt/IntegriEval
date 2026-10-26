"use client";

import { useState } from "react";
import { getToken, request } from "@/lib/api";
import Dialog from "./Dialog";
import { Banner, Button, FormStack, MutedText, surfacePanelClasses } from "./ui";

export default function EvaluationOperations({
  courseId,
  evaluation,
  onChanged,
}: {
  courseId: number;
  evaluation: any;
  onChanged: () => void | Promise<void>;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [mail, setMail] = useState<any[] | null>(null);
  const key = evaluation.id < 0 ? -evaluation.id : 0;
  const root = `/asignaturas/${courseId}`;

  const exportFile = async (format: string) => {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(
        `/api${root}/exportar?formato=${format}${key ? "&actividad_id=" + key : ""}`,
        { headers: { Authorization: "Bearer " + getToken() } },
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "No se pudo exportar");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `resultados-${courseId}-${key}.${format}`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const changeState = async (value: string) => {
    if (!confirm(`¿Cambiar esta evaluación a «${value}»? Se conserva todo su historial.`)) return;
    setBusy(true);
    setError("");
    try {
      await request(`${root}/actividades/${key}/estado`, "PUT", { estado: value });
      await onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const openMail = async () => {
    setError("");
    try {
      setMail(await request(root + "/correos"));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const retryMail = async (item: any) => {
    setBusy(true);
    try {
      await request(`${root}/correos/${item.id}/reintentar`, "POST");
      await openMail();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const state = evaluation.estado || "abierta";

  return (
    <section className={surfacePanelClasses} aria-label="Operaciones de la evaluación">
      <div className="flex flex-wrap items-center gap-4">
        <strong>
          {evaluation.title} · {state}
        </strong>
        <Button variant="surface" size="classic" disabled={busy} onClick={() => exportFile("csv")}>
          Exportar CSV / Excel
        </Button>
        <Button variant="surface" size="classic" disabled={busy} onClick={() => exportFile("pdf")}>
          Exportar PDF
        </Button>
        <Button variant="surface" size="classic" disabled={busy} onClick={openMail}>
          Historial de correos
        </Button>
        {state === "abierta" ? (
          <>
            <Button
              variant="surface"
              size="classic"
              disabled={busy}
              onClick={() => changeState("cerrada")}
            >
              Cerrar evaluación
            </Button>
            <Button
              variant="surface"
              size="classic"
              disabled={busy}
              onClick={() => changeState("archivada")}
            >
              Archivar
            </Button>
          </>
        ) : (
          <Button
            variant="surface"
            size="classic"
            disabled={busy}
            onClick={() => changeState("abierta")}
          >
            Reabrir evaluación
          </Button>
        )}
      </div>
      {evaluation.estado && evaluation.estado !== "abierta" && (
        <MutedText>El historial sigue disponible. Reabre la evaluación para modificar sus datos.</MutedText>
      )}
      {error && (
        <Banner tone="error" role="alert">
          {error}
        </Banner>
      )}
      {mail && (
        <Dialog title="Historial de correos del curso" wide onClose={() => setMail(null)}>
          <FormStack>
            <p>
              Los envíos aparecen desde que se habilitó este registro. Un estado «disabled» significa
              que SMTP está desactivado; el correo no se ha enviado.
            </p>
            {mail.length === 0 ? (
              <p>No hay envíos registrados.</p>
            ) : (
              mail.map((item) => (
                <article key={item.id} className={surfacePanelClasses}>
                  <strong>{item.subject}</strong>
                  <p>
                    {item.recipient} · {item.status} · {item.attempts} intentos
                  </p>
                  {item.error && <p>{item.error}</p>}
                  {["failed", "disabled", "pending"].includes(item.status) && (
                    <Button
                      variant="surface"
                      size="classic"
                      disabled={busy}
                      onClick={() => retryMail(item)}
                    >
                      Reintentar envío
                    </Button>
                  )}
                </article>
              ))
            )}
          </FormStack>
        </Dialog>
      )}
    </section>
  );
}
