"use client";

import type { FormEvent } from "react";
import { Calendar, Clock, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "../DashboardContext";
import { Button, EmptyNote, Field, Hint, Input, Panel, SectionTitle, Select } from "../ui";

const DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

export default function AvailabilityTab() {
  const { availabilities, loadAvailabilities, setError, setSuccess } = useDashboard();
  const [day, setDay] = usePersistentState("availability.day", 0);
  const [start, setStart] = usePersistentState("availability.start", "09:00");
  const [end, setEnd] = usePersistentState("availability.end", "11:00");

  const add = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api.addTeacherAvailability({
        day_of_week: Number(day),
        start_time: start,
        end_time: end,
      });
      setSuccess("Horario de disponibilidad agregado.");
      loadAvailabilities();
    } catch (err: any) {
      setError(err.message || "Error al agregar horario");
    }
  };

  const remove = async (id: number) => {
    try {
      await api.deleteTeacherAvailability(id);
      loadAvailabilities();
    } catch (err: any) {
      setError("Error al eliminar horario");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <Panel>
        <SectionTitle icon={Clock}>Agregar Bloque Horario</SectionTitle>
        <Hint>
          El sistema usará estos bloques semanales para agendar automáticamente las defensas de los
          alumnos convocados.
        </Hint>

        <form onSubmit={add} className="space-y-3 text-xs">
          <Field label="Día de la Semana">
            <Select value={day} onChange={(e) => setDay(Number(e.target.value))}>
              <option value={0}>Lunes</option>
              <option value={1}>Martes</option>
              <option value={2}>Miércoles</option>
              <option value={3}>Jueves</option>
              <option value={4}>Viernes</option>
            </Select>
          </Field>

          <div className="grid grid-cols-2 gap-2">
            <Field label="Inicio (HH:MM)">
              <Input type="time" value={start} onChange={(e) => setStart(e.target.value)} />
            </Field>
            <Field label="Fin (HH:MM)">
              <Input type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
            </Field>
          </div>

          <Button type="submit" size="block">
            Agregar Horario
          </Button>
        </form>
      </Panel>

      <Panel className="md:col-span-2">
        <SectionTitle icon={Calendar}>
          Mis Horarios de Atención Semanales ({availabilities.length})
        </SectionTitle>

        {availabilities.length === 0 ? (
          <EmptyNote>
            No has registrado horarios. Puedes elegir la fecha y hora al agendar cada cita.
          </EmptyNote>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {availabilities.map((av) => (
              <div
                key={av.id}
                className="flex items-center justify-between rounded-control border border-line bg-raised p-3.5 text-xs"
              >
                <div>
                  <span className="text-sm font-bold text-fg">{DAY_NAMES[av.day_of_week] || ""}</span>
                  <p className="mt-0.5 font-mono text-muted">
                    {av.start_time} - {av.end_time} hrs
                  </p>
                </div>
                <Button variant="danger" className="p-1.5" onClick={() => remove(av.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
