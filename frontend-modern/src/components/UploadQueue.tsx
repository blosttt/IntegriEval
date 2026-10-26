"use client";

import { useEffect, useRef, useState } from "react";
import { request } from "@/lib/api";
import { Banner, Button, MutedText, courseRowClasses, surfacePanelClasses } from "./ui";

export default function UploadQueue({
  courseId,
  evaluationId,
  onCompleted,
}: {
  courseId: number;
  evaluationId: number;
  onCompleted: () => void;
}) {
  const [jobs, setJobs] = useState<any[]>([]);
  const [error, setError] = useState("");
  const callback = useRef(onCompleted);
  callback.current = onCompleted;
  const completed = useRef("");
  const activity = evaluationId < 0 ? -evaluationId : 0;
  const root = `/asignaturas/${courseId}/cargas`;
  const labels: any = {
    pending: "En cola",
    running: "Procesando",
    completed: "Completado",
    failed: "Error",
    cancelled: "Cancelado",
  };

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    completed.current = "";
    const load = async () => {
      try {
        const data = await request(root + (activity ? "?actividad_id=" + activity : ""));
        if (!active) return;
        setJobs(data);
        const signature = data
          .filter((j: any) => j.status === "completed")
          .map((j: any) => `${j.id}:${j.attempts}`)
          .join(",");
        if (completed.current && completed.current !== signature) callback.current();
        if (!completed.current && signature) callback.current();
        completed.current = signature;
      } catch (e: any) {
        if (active) setError(e.message);
      }
      if (active) timer = setTimeout(load, 3000);
    };
    load();
    const refresh = () => {
      clearTimeout(timer);
      load();
    };
    window.addEventListener("integryeval:uploads-queued", refresh);
    return () => {
      active = false;
      clearTimeout(timer);
      window.removeEventListener("integryeval:uploads-queued", refresh);
    };
  }, [courseId, evaluationId]);

  const finished = jobs.filter((j) => ["completed", "failed", "cancelled"].includes(j.status)).length;

  const act = async (job: any) => {
    try {
      const result = await request(
        `${root}/${job.id}/${job.status === "pending" ? "cancelar" : "reintentar"}`,
        "POST",
      );
      setJobs((items) => items.map((j) => (j.id === job.id ? result : j)));
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <section className={surfacePanelClasses}>
      <h3 className="text-[15px] font-semibold">Procesamiento de archivos</h3>
      <p>
        {jobs.length
          ? `${finished} de ${jobs.length} archivos finalizados`
          : "No hay archivos en cola para esta evaluación."}
      </p>
      {!!jobs.length && (
        <progress
          aria-label="Archivos finalizados"
          value={finished}
          max={jobs.length}
          className="w-full"
        />
      )}
      <MutedText>
        Puedes cancelar los archivos pendientes. Los que ya empezaron terminan su procesamiento.
      </MutedText>
      {error && (
        <Banner tone="error" role="alert">
          {error}
        </Banner>
      )}
      {jobs.map((job) => (
        <article className={courseRowClasses()} key={job.id}>
          <div>
            <strong>{job.filename}</strong>
            <p>
              {labels[job.status] || job.status} · intento {job.attempts}
              {job.error ? " · " + job.error : ""}
            </p>
          </div>
          {["pending", "failed", "cancelled"].includes(job.status) && (
            <Button variant="surface" size="classic" onClick={() => act(job)}>
              {job.status === "pending" ? "Cancelar" : "Reintentar"}
            </Button>
          )}
        </article>
      ))}
    </section>
  );
}
