"use client";

import type { FormEvent } from "react";
import { FileText, Sliders } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import { Button, Field, Hint, Input, Panel, SectionTitle, Select, Textarea, selectableCard } from "../ui";

export default function EvaluationsTab() {
  const {
    selectedCourseId,
    selectedEvalId,
    setSelectedEvalId,
    selectedEval,
    setSelectedEval,
    courseEvals,
    setCourseEvals,
    creatingEval,
    setCreatingEval,
    evalForm,
    patchEvalForm,
    setError,
    setSuccess,
    openTab,
  } = useDashboard();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      const save = creatingEval ? api.createEvaluation : api.updateEvaluation;
      const created = await save(creatingEval ? selectedCourseId : selectedEvalId!, {
        title: evalForm.title,
        prompt_rubric: evalForm.rubric,
        question_rigor: evalForm.rigor,
        pool_size: Number(evalForm.poolSize),
        flash_questions_count: Number(evalForm.flashCount),
        time_per_question: Number(evalForm.time),
        low_threshold: Number(evalForm.low),
        high_threshold: Number(evalForm.high),
        random_review_pct: Number(evalForm.randomPct),
      });
      setSuccess(creatingEval ? "Evaluación creada." : "Evaluación actualizada.");
      setCreatingEval(false);
      setSelectedEval(created);
      setCourseEvals(await api.getCourseEvaluations(selectedCourseId));
      setSelectedEvalId(created.id);
      openTab("materials", { courseId: selectedCourseId, evalId: created.id });
    } catch (err: any) {
      setError(err.message || "Error al crear evaluación");
    }
  };

  const startCreating = () => {
    setCreatingEval(true);
    patchEvalForm({ title: "", rubric: "" });
  };

  const cancelCreating = () => {
    setCreatingEval(false);
    if (selectedEval) patchEvalForm({ title: selectedEval.title, rubric: selectedEval.prompt_rubric });
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Panel size="lg" className="lg:col-span-2">
        <SectionTitle icon={Sliders}>
          {creatingEval ? "Nueva evaluación" : "Parámetros de la evaluación seleccionada"}
        </SectionTitle>
        <Hint>
          Define la pauta de corrección y el rigor del análisis. La IA evaluará los trabajos basándose en
          estas directrices.
        </Hint>

        <form onSubmit={submit} className="space-y-4 text-xs">
          <Field label="Título de la Evaluación">
            <Input
              type="text"
              required
              placeholder="ej. Informe Final de Investigación Interdisciplinaria"
              value={evalForm.title}
              onChange={(e) => patchEvalForm({ title: e.target.value })}
            />
          </Field>

          <Field label="Prompt / Pauta de Corrección para la IA">
            <Textarea
              rows={4}
              placeholder="Describe los criterios de evaluación: metodología, conclusiones, profundidad técnica, uso de fuentes..."
              data-tour="rubric"
              value={evalForm.rubric}
              onChange={(e) => patchEvalForm({ rubric: e.target.value })}
            />
          </Field>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Field label="Rigor de Preguntas">
              <Select value={evalForm.rigor} onChange={(e) => patchEvalForm({ rigor: e.target.value })}>
                <option value="high">Estricto (Detalles y citas exactas)</option>
                <option value="medium">Medio (Conceptos y metodología)</option>
                <option value="low">Laxo (Comprensión general)</option>
              </Select>
            </Field>

            <Field label="Pool Total de Preguntas">
              <Input
                type="number"
                data-tour="question-settings"
                value={evalForm.poolSize}
                onChange={(e) => patchEvalForm({ poolSize: Number(e.target.value) })}
              />
            </Field>

            <Field label="Preguntas para el Flash Test">
              <Input
                type="number"
                value={evalForm.flashCount}
                onChange={(e) => patchEvalForm({ flashCount: Number(e.target.value) })}
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <Field label="Tiempo por Pregunta (seg)">
              <Input
                type="number"
                value={evalForm.time}
                onChange={(e) => patchEvalForm({ time: Number(e.target.value) })}
              />
            </Field>

            <Field label="Coherencia mínima (0–1)">
              <Input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={evalForm.low}
                onChange={(e) => patchEvalForm({ low: Number(e.target.value) })}
              />
            </Field>

            <Field label="Umbral de alerta IA (0–1)">
              <Input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={evalForm.high}
                onChange={(e) => patchEvalForm({ high: Number(e.target.value) })}
              />
            </Field>
          </div>

          <Button type="submit" size="blockLg">
            {creatingEval ? "Crear evaluación" : "Guardar evaluación"}
          </Button>
        </form>
      </Panel>

      <Panel>
        <SectionTitle icon={FileText}>Evaluaciones de la asignatura</SectionTitle>
        <Button size="classic" onClick={startCreating}>
          Nueva evaluación
        </Button>
        {creatingEval && (
          <Button variant="surface" size="classic" onClick={cancelCreating}>
            Cancelar creación
          </Button>
        )}
        <div className="space-y-3">
          {courseEvals.map((ev) => (
            <div
              key={ev.id}
              onClick={() => setSelectedEvalId(ev.id)}
              className={selectableCard(selectedEvalId === ev.id, "p-3.5")}
            >
              <h4 className="text-xs font-bold text-fg">{ev.title}</h4>
              <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-muted">
                <span className="rounded bg-raised px-2 py-0.5 text-fg">Rigor: {ev.question_rigor}</span>
                <span className="rounded bg-raised px-2 py-0.5 text-fg">Pool: {ev.pool_size}</span>
                <span className="rounded bg-raised px-2 py-0.5 text-fg">Flash: {ev.flash_questions_count}</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
