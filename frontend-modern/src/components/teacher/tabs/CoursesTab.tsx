"use client";

import { BookOpen } from "lucide-react";
import { useDashboard } from "../DashboardContext";
import { EmptyState, Hint, Panel, SectionTitle, selectableCard } from "../ui";

export default function CoursesTab() {
  const { courses, selectedCourseId, setSelectedCourseId } = useDashboard();
  return (
    <div className="grid grid-cols-1 gap-6">
      <Panel>
        <SectionTitle icon={BookOpen}>Asignaturas asignadas</SectionTitle>
        {!courses.length && (
          <EmptyState>
            Aún no tienes asignaturas asignadas. Solicita al administrador que te dé acceso a un curso.
          </EmptyState>
        )}
        <Hint>
          El administrador crea las asignaturas y asigna a sus docentes. Puedes trabajar con la nómina,
          materiales e informes de tus cursos.
        </Hint>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {courses.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedCourseId(c.id)}
              className={selectableCard(selectedCourseId === c.id)}
            >
              <div className="flex items-start justify-between">
                <h4 className="text-sm font-bold text-fg">{c.name}</h4>
                <span className="rounded bg-raised px-2 py-0.5 font-mono text-[10px] text-fg">
                  {c.period}
                </span>
              </div>
              <p className="mt-2 text-xs text-muted">
                Estudiantes registrados:{" "}
                <span className="font-semibold text-brand-ink">{c.student_count || 0}</span>
              </p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
