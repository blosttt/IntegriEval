"use client";

import {
  BarChart3,
  BookOpen,
  Calendar,
  FileText,
  FileUp,
  HelpCircle,
  Sliders,
  UserCheck,
  Users,
} from "lucide-react";
import { useDashboard } from "./DashboardContext";
import { colorTransition, cx } from "./ui";
import type { IconType, TabId } from "./types";

const TABS: { id: TabId; label: string; icon: IconType }[] = [
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
      {TABS.map((tab) => {
        const Icon = tab.icon;
        const active = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            data-tour={`tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={cx(
              "flex items-center gap-1.5 rounded-t-xl border-b-2 px-4 py-2.5 font-semibold whitespace-nowrap",
              colorTransition,
              active
                ? "border-brand bg-brand-soft text-brand-ink"
                : "border-line bg-raised text-muted",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
