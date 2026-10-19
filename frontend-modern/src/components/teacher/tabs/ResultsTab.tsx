"use client";

import { useState, type ReactNode } from "react";
import { AlertTriangle, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import { Button, DataTable, Hint, Input, Panel, SectionTitle, cx } from "../ui";

const pct = (value: number | null | undefined) =>
  value != null ? `${Math.round(value * 100)}%` : "--";

function Stat({ label, value, tone = "text-fg" }: { label: string; value: ReactNode; tone?: string }) {
  return (
    <Panel size="sm" stack={false} radius="control">
      <span className="text-[10px] font-bold uppercase text-muted">{label}</span>
      <p className={cx("mt-1 text-2xl font-bold", tone)}>{value}</p>
    </Panel>
  );
}

export default function ResultsTab() {
  const {
    evalStats, reviewList, reports, selectedEvalId, scheduleDefense, loadEvalSubData, setError, setSuccess,
  } = useDashboard();

  const [scoreOverrides, setScoreOverrides] = useState<Record<number, string>>({});

  const handleScoreOverride = async (reportId: number) => {
    const sid = reports.find((r: any) => r.id === reportId)?.student_id;
    const num = parseFloat(scoreOverrides[sid] || "");
    if (isNaN(num) || num < 0 || num > 1) {
      setError("La nota debe ser un decimal entre 0.0 y 1.0 (ej. 0.85 = 85%)");
      return;
    }
    try {
      const reason = window.prompt("Justificación pedagógica del logro final:");
      if (!reason?.trim()) {
        setError("Debe indicar una justificación pedagógica");
        return;
      }
      await api.updateReportScore(reportId, num, reason);
      setSuccess("Nota actualizada correctamente.");
      setScoreOverrides((previous) => ({ ...previous, [sid]: "" }));
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al modificar nota");
    }
  };

  return (
    <div className="space-y-6">
      {evalStats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <Stat label="Promedio IA" value={pct(evalStats.avg_ai_score)} />
          <Stat label="Flash Tests Rendidos" value={evalStats.flash_test?.completed || 0} />
          <Stat label="Convocados a Oficina" value={reviewList.length} tone="text-yellow-400" />
          <Stat label="Citas Pendientes" value={evalStats.appointments?.pending || 0} tone="text-brand-ink" />
        </div>
      )}

      <Panel size="lg" className="border-yellow-500/30 bg-yellow-950/10">
        <SectionTitle icon={AlertTriangle} iconClassName="text-yellow-400" className="text-yellow-300">
          Lista de Convocatoria a Oficina ({reviewList.length})
        </SectionTitle>
        <Hint>
          Alumnos que requieren revisión por sus indicadores de análisis o Flash Test. Elige la fecha y el
          horario de cada cita; no se agenda automáticamente.
        </Hint>

        {reviewList.length === 0 ? (
          <p className="py-4 text-xs italic text-muted">No hay estudiantes convocados a oficina por ahora.</p>
        ) : (
          <DataTable headPadding="pb-2" columns={["Estudiante", "Motivo", "Nota IA", "Flash Score", "Cita"]}>
            {reviewList.map((item, i) => (
              <tr key={i}>
                <td className="py-2.5 font-bold text-fg">
                  {item.student_name}
                  <br />
                  <button
                    type="button"
                    className="text-xs text-brand-ink"
                    onClick={() => scheduleDefense(item.student_id)}
                  >
                    Agendar defensa
                  </button>
                </td>
                <td className="py-2.5">
                  <span className="rounded bg-yellow-950 px-2 py-0.5 font-mono text-[10px] text-yellow-300">
                    {item.review_reason}
                  </span>
                </td>
                <td className="py-2.5 text-fg">{pct(item.ai_score)}</td>
                <td className="py-2.5 text-fg">{pct(item.flash_score)}</td>
                <td className="py-2.5 font-semibold text-brand-ink">
                  {item.appointment_time
                    ? new Date(item.appointment_time).toLocaleString("es-CL", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "Agendando..."}
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Panel>

      <Panel size="lg">
        <SectionTitle icon={Users} data-tour="results">
          Calificaciones Finales y Ajustes
        </SectionTitle>
        <DataTable
          columns={[
            "Estudiante",
            "Nota Preliminar IA",
            "Flash Test",
            "Calificación Final",
            { label: "Ajuste Manual", align: "right" },
          ]}
        >
          {evalStats?.students?.map((st: any) => (
            <tr key={st.student_id}>
              <td className="py-3 font-semibold text-fg">{st.student_name}</td>
              <td className="py-3 text-fg">{pct(st.ai_score)}</td>
              <td className="py-3">
                {st.flash_score != null ? (
                  <span className="font-bold text-brand-ink">{pct(st.flash_score)}</span>
                ) : (
                  <span className="text-muted">Pendiente</span>
                )}
              </td>
              <td className="py-3 text-sm font-bold text-emerald-400">
                {st.final_score != null ? pct(st.final_score) : pct(st.ai_score)}
              </td>
              <td className="py-3 text-right">
                <div className="inline-flex items-center gap-1.5">
                  <Input
                    density="tiny"
                    fill={false}
                    className="w-16 text-[11px]"
                    type="number"
                    step="0.01"
                    placeholder="0.0-1.0"
                    value={scoreOverrides[st.student_id] || ""}
                    onChange={(e) =>
                      setScoreOverrides((previous) => ({ ...previous, [st.student_id]: e.target.value }))
                    }
                  />
                  <Button
                    variant="secondary"
                    className="rounded px-2 py-1 text-[10px] font-bold"
                    onClick={() => {
                      const rep = reports.find((r) => r.student_id === st.student_id);
                      if (rep) handleScoreOverride(rep.id);
                    }}
                  >
                    Guardar
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </DataTable>
      </Panel>
    </div>
  );
}
