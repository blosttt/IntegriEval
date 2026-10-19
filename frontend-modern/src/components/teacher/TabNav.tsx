"use client";

import {
  BarChart3, BookOpen, Calendar, FileText, FileUp, HelpCircle, Sliders, UserCheck, Users,
} from "lucide-react";
import { useDashboard } from "./DashboardContext";
import { cx } from "./ui";
import type { IconType, TabId } from "./types";

export const TABS: Array<{ id: TabId; label: string; icon: IconType }> = [
  { id: "courses", label: "1. Cursos", icon: BookOpen },
  { id: "students", label: "2. Estudiantes (Roster)", icon: Users },
  { id: "evaluations", label: "3. Parámetros Evaluación", icon: Sliders },
  { id: "materials", label: "4. Materiales de Apoyo", icon: FileText },
  { id: "reports", label: "5. Trabajos & Análisis IA", icon: FileUp },
  { id: "questions", label: "6. Pool de Preguntas", icon: HelpCircle },
  { id: "results", label: "7. Resultados & Citas", icon: BarChart3 },
  { id: "appointments", label: "8. Citas de Oficina", icon: UserCheck },
  { id: "availability", label: "9. Disponibilidad", icon: Calendar },
];

export default function TabNav() {
  const { activeTab, setActiveTab } = useDashboard();

  return (
    <div className="flex gap-1 overflow-x-auto border-b border-line pb-1 text-xs">
      {TABS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          data-tour={`tab-${id}`}
          onClick={() => setActiveTab(id)}
          className={cx(
            "flex items-center gap-1.5 whitespace-nowrap rounded-t-control border-b-2 px-4 py-2.5 font-semibold transition-all",
            activeTab === id
              ? "border-brand bg-brand-soft text-brand-ink"
              : "border-transparent text-muted hover:bg-raised hover:text-fg",
          )}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </button>
      ))}
    </div>
  );
}
