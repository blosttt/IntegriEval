"use client";

import { BookOpen, Sparkles } from "lucide-react";
import { useDashboard } from "./DashboardContext";
import { Button, Panel, Select, btnClassic } from "./ui";

export default function DashboardHeader() {
  const {
    accountRole, adminTeacher, courses, selectedCourseId, selectCourse,
    courseEvals, selectedEvalId, selectEvaluation,
  } = useDashboard();

  const title = adminTeacher
    ? `Espacio de ${adminTeacher.nombre}`
    : accountRole === "ayudante"
      ? "Panel de Evaluación · Ayudante"
      : "Panel de Evaluación Docente";

  return (
    <>
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted">
          {accountRole === "ayudante"
            ? "Ayudantía · Nómina de solo lectura"
            : "Docencia · Cursos asignados"}
        </span>
        <Button
          variant="surface"
          className={btnClassic}
          onClick={() => window.dispatchEvent(new Event("integryeval:open-tutorial"))}
        >
          <BookOpen size={16} />
          Guía de uso
        </Button>
      </div>

      <Panel stack={false} className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-fg">
            <Sparkles className="h-5 w-5 text-brand-ink" />
            {title}
          </h1>
          <p className="mt-0.5 text-xs text-muted">
            Gestión semi-automatizada: análisis con IA, pool de preguntas y defensa flash.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-muted">Curso:</span>
            <Select
              density="header"
              fill={false}
              data-tour="course-selector"
              aria-label="Asignatura activa"
              value={selectedCourseId || ""}
              onChange={(e) => selectCourse(Number(e.target.value))}
            >
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.period})
                </option>
              ))}
            </Select>
          </div>

          {courseEvals.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted">Evaluación:</span>
              <Select
                density="header"
                fill={false}
                className="font-medium text-brand-ink"
                aria-label="Evaluación activa"
                value={selectedEvalId || ""}
                onChange={(e) => selectEvaluation(Number(e.target.value))}
              >
                {courseEvals.map((ev) => (
                  <option key={ev.id} value={ev.id}>
                    {ev.title}
                  </option>
                ))}
              </Select>
            </div>
          )}
        </div>
      </Panel>
    </>
  );
}
