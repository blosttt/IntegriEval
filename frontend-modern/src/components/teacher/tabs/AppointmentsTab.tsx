"use client";

import React, { useState } from "react";
import { Calendar, Clock, Edit } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import {
  Button, EmptyNote, Field, Input, Panel, Select, SectionTitle, Textarea,
  btnBlockLg, btnClassic, cx, selectableCard,
} from "../ui";

export default function AppointmentsTab() {
  const {
    appointments, students, selectedCourseId, activityId, setAppointmentDraft,
    loadAppointments, loadEvalSubData, selectedEvalId, setError, setSuccess,
  } = useDashboard();

  const [selected, setSelected] = useState<any | null>(null);
  const [status, setStatus] = useState("completed");
  const [notes, setNotes] = useState("");
  const [adjustedScore, setAdjustedScore] = useState("");

  const visible = appointments.filter(
    (a) => a.course_id === selectedCourseId && (a.actividad_id || null) === activityId,
  );

  const select = (appt: any) => {
    setSelected(appt);
    setStatus(appt.status === "cancelled" ? "cancelled" : "completed");
    setNotes(appt.notes || "");
    setAdjustedScore("");
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;
    try {
      await api.submitAppointmentFeedback(selected.id, {
        status,
        notes,
        adjusted_score: adjustedScore !== "" ? parseFloat(adjustedScore) : null,
      });
      setSuccess("Cita registrada y calificación final actualizada.");
      setSelected(null);
      setNotes("");
      setAdjustedScore("");
      loadAppointments();
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al guardar feedback");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <Panel size="lg" className="md:col-span-2">
        <SectionTitle icon={Calendar} data-tour="appointments">
          Citas de revisión ({visible.length})
        </SectionTitle>

        <Button className={`${btnClassic} border border-brand`} disabled={!students.length} onClick={() => setAppointmentDraft({})}>
          Agendar revisión
        </Button>

        {visible.length === 0 ? (
          <EmptyNote>No hay citas de oficina agendadas actualmente.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {visible.map((appt) => (
              <div
                key={appt.id}
                onClick={() => select(appt)}
                className={selectableCard(selected?.id === appt.id)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-fg">{appt.student_name}</h4>
                    <p className="text-xs text-muted">{appt.evaluation_title}</p>
                  </div>
                  <span
                    className={cx(
                      "rounded px-2 py-0.5 text-[10px] font-semibold",
                      appt.status === "pending"
                        ? "bg-yellow-950 text-yellow-300"
                        : "bg-emerald-950 text-emerald-300",
                    )}
                  >
                    {appt.status === "pending" ? "Pendiente" : "Completada"}
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs text-muted">
                  <Clock className="h-3.5 w-3.5 text-brand-ink" />
                  {new Date(appt.scheduled_time).toLocaleString("es-CL", {
                    weekday: "long",
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
                <Button
                  variant="surface"
                  className={btnClassic}
                  onClick={(e) => {
                    e.stopPropagation();
                    setAppointmentDraft(appt);
                  }}
                >
                  Cambiar fecha y hora
                </Button>
                {appt.notes && <p className="mt-2 text-[11px] italic text-muted">{appt.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel size="lg">
        <SectionTitle icon={Edit}>Registrar Resultado de Cita</SectionTitle>
        {selected ? (
          <form onSubmit={handleSubmitFeedback} className="space-y-4 text-xs">
            <div>
              <span className="block text-[10px] text-muted">Estudiante</span>
              <p className="text-sm font-bold text-fg">{selected.student_name}</p>
            </div>

            <Field label="Estado de la Cita">
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="completed">Completada (Reunión realizada)</option>
                <option value="cancelled">Cancelada / No asistió</option>
              </Select>
            </Field>

            <Field label="Ajustar Calificación Final (0.0 a 1.0)">
              <Input
                type="number"
                min="0"
                max="1"
                step="0.05"
                placeholder="ej. 0.90 (90%) si justificó bien"
                value={adjustedScore}
                onChange={(e) => setAdjustedScore(e.target.value)}
              />
            </Field>

            <Field label="Notas / Justificación">
              <Textarea
                rows={3}
                placeholder="El estudiante explicó detalladamente la metodología y resolvió las dudas..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </Field>

            <Button type="submit" className={btnBlockLg}>
              Guardar y Cerrar Cita
            </Button>
          </form>
        ) : (
          <EmptyNote>
            Selecciona una cita de la lista para registrar el resultado y modificar la calificación.
          </EmptyNote>
        )}
      </Panel>
    </div>
  );
}
