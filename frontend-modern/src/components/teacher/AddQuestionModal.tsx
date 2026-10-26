"use client";

import type { FormEvent } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "./DashboardContext";
import { Button, Field, Input, ModalFrame, Select, Textarea } from "./ui";

export default function AddQuestionModal({ onClose }: { onClose: () => void }) {
  const { selectedReportId, selectedEval, setSuccess, setError, setQuestionBank } = useDashboard();
  const [text, setText] = usePersistentState("question.text", "");
  const [type, setType] = usePersistentState<"multiple_choice" | "true_false">(
    "question.type",
    "multiple_choice",
  );
  const [options, setOptions] = usePersistentState<string[]>("question.options", ["", "", "", ""]);
  const [correct, setCorrect] = usePersistentState("question.correct", "0");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedReportId || !text) return;
    try {
      await api.createQuestion(selectedReportId, {
        text,
        type,
        options: type === "multiple_choice" ? options : ["Verdadero", "Falso"],
        correct_answer: correct,
        limit_seconds: selectedEval?.time_per_question || 30,
      });
      setSuccess("Pregunta agregada al pool.");
      onClose();
      setText("");
      setOptions(["", "", "", ""]);
      setCorrect("0");
      setQuestionBank(await api.getQuestionBank(selectedReportId));
    } catch (err: any) {
      setError(err.message || "Error al crear pregunta");
    }
  };

  return (
    <ModalFrame className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-fg">Agregar Pregunta Personalizada al Pool</h3>
        <Button variant="muted" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <form onSubmit={submit} className="space-y-3">
        <Field label="Enunciado de la Pregunta">
          <Textarea
            rows={2}
            required
            placeholder="¿Cuál fue el resultado obtenido en la sección 3.2?"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </Field>

        <Field label="Tipo de Pregunta">
          <Select value={type} onChange={(e) => setType(e.target.value as "multiple_choice" | "true_false")}>
            <option value="multiple_choice">Selección Múltiple (4 alternativas)</option>
            <option value="true_false">Verdadero / Falso</option>
          </Select>
        </Field>

        {type === "multiple_choice" && (
          <div className="space-y-2">
            <span className="block font-bold text-fg">Alternativas y Respuesta Correcta</span>
            {options.map((option, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="font-bold text-muted">{String.fromCharCode(65 + i)})</span>
                <Input
                  density="sm"
                  type="text"
                  required
                  placeholder={`Opción ${String.fromCharCode(65 + i)}`}
                  value={option}
                  className="flex-1"
                  fill={false}
                  onChange={(e) => {
                    const next = [...options];
                    next[i] = e.target.value;
                    setOptions(next);
                  }}
                />
                <input
                  type="radio"
                  name="correct-ans"
                  checked={correct === String(i)}
                  onChange={() => setCorrect(String(i))}
                  className="h-4 w-4"
                  title="Marcar como correcta"
                />
              </div>
            ))}
          </div>
        )}

        {type === "true_false" && (
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-fg">
              <input
                type="radio"
                name="correct-tf"
                checked={correct === "0"}
                onChange={() => setCorrect("0")}
              />
              Verdadero es la correcta
            </label>
            <label className="flex items-center gap-2 text-fg">
              <input
                type="radio"
                name="correct-tf"
                checked={correct === "1"}
                onChange={() => setCorrect("1")}
              />
              Falso es la correcta
            </label>
          </div>
        )}

        <Button type="submit" size="block" className="py-2.5">
          Guardar Pregunta
        </Button>
      </form>
    </ModalFrame>
  );
}
