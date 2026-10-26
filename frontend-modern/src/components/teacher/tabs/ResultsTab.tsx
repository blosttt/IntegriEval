"use client";

import { AlertTriangle, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "../DashboardContext";
import { Button, DataTable, EmptyNote, Hint, Input, Panel, SectionTitle } from "../ui";

const percent = (value: number | null | undefined) =>
  value != null ? `${Math.round(value * 100)}%` : "--";

function StatCard({ label, value, tone = "text-fg" }: { label: string; value: string | number; tone?: string }) {
  return (
    <Panel size="sm" radius="control" stack={false}>
      <span className="text-[10px] font-bold text-muted uppercase">{label}</span>
      <p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p>
    </Panel>
  );
}

export default function ResultsTab() {
  const {
    evalStats,
    reviewList,
    reports,
    selectedEvalId,
    loadEvalSubData,
    setAppointmentDraft,
    setError,
    setSuccess,
  } = useDashboard();
  const [overrides, setOverrides] = usePersistentState<Record<number, string>>("results.overrides", {});

  const overrideScore = async (reportId: number) => {
    const studentId = reports.find((r: any) => r.id === reportId)?.student_id;
    const value = parseFloat(overrides[studentId] || "");
    if (isNaN(value) || value < 0 || value > 1) {
      setError("La nota debe ser un decimal entre 0.0 y 1.0 (ej. 0.85 = 85%)");
      return;
    }
    try {
      const reason = window.prompt("Justificación pedagógica del logro final:");
      if (!reason?.trim()) {
        setError("Debe indicar una justificación pedagógica");
        return;
      }
      await api.updateReportScore(reportId, value, reason);
      setSuccess("Nota actualizada correctamente.");
      setOverrides((previous) => ({ ...previous, [studentId]: "" }));
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al modificar nota");
    }
  };

  return (
    <div className="space-y-6">
      {evalStats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <StatCard label="Promedio IA" value={percent(evalStats.avg_ai_score)} />
          <StatCard label="Flash Tests Rendidos" value={evalStats.flash_test?.completed || 0} />
          <StatCard label="Convocados a Oficina" value={reviewList.length} tone="text-yellow-400" />
          <StatCard label="Citas Pendientes" value={evalStats.appointments?.pending || 0} tone="text-brand-ink" />
        </div>
      )}

      <Panel size="lg">
        <SectionTitle icon={AlertTriangle} tone="text-yellow-300" iconTone="text-yellow-400">
          Lista de Convocatoria a Oficina ({reviewList.length})
        </SectionTitle>
        <Hint>
          Alumnos que requieren revisión por sus indicadores de análisis o Flash Test. Elige la fecha y el
          horario de cada cita; no se agenda automáticamente.
        </Hint>

        {reviewList.length === 0 ? (
          <EmptyNote className="py-4">No hay estudiantes convocados a oficina por ahora.</EmptyNote>
        ) : (
          <DataTable headPadding="pb-2" columns={["Estudiante", "Motivo", "Nota IA", "Flash Score", "Cita"]}>
            {reviewList.map((item, i) => (
              <tr key={i}>
                <td className="py-2.5 font-bold text-fg">
                  {item.student_name}
                  <br />
                  <Button
                    variant="link"
                    className="text-xs"
                    onClick={() => setAppointmentDraft({ estudiante_id: item.student_id })}
                  >
                    Agendar defensa
                  </Button>
                </td>
                <td className="py-2.5">
                  <span className="rounded bg-yellow-950 px-2 py-0.5 font-mono text-[10px] text-yellow-300">
                    {item.review_reason}
                  </span>
                </td>
                <td className="py-2.5 text-fg">{percent(item.ai_score)}</td>
                <td className="py-2.5 text-fg">{percent(item.flash_score)}</td>
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
              <td className="py-3 text-fg">{percent(st.ai_score)}</td>
              <td className="py-3">
                {st.flash_score != null ? (
                  <span className="font-bold text-brand-ink">{Math.round(st.flash_score * 100)}%</span>
                ) : (
                  <span className="text-muted">Pendiente</span>
                )}
              </td>
              <td className="py-3 text-sm font-bold text-emerald-400">
                {st.final_score != null ? percent(st.final_score) : percent(st.ai_score)}
              </td>
              <td className="py-3 text-right">
                <div className="inline-flex items-center gap-1.5">
                  <Input
                    density="tiny"
                    fill={false}
                    className="w-16"
                    type="number"
                    step="0.01"
                    placeholder="0.0-1.0"
                    value={overrides[st.student_id] || ""}
                    onChange={(e) =>
                      setOverrides((previous) => ({ ...previous, [st.student_id]: e.target.value }))
                    }
                  />
                  <Button
                    variant="secondary"
                    size="mini"
                    onClick={() => {
                      const report = reports.find((r) => r.student_id === st.student_id);
                      if (report) overrideScore(report.id);
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
