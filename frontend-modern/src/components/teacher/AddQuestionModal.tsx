"use client";

import React, { useState } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Field, Input, ModalFrame, Select, Textarea, cx } from "./ui";

type QuestionType = "multiple_choice" | "true_false";

export default function AddQuestionModal({
  reportId,
  limitSeconds,
  onClose,
  onCreated,
  onError,
}: {
  reportId: number;
  limitSeconds: number;
  onClose: () => void;

  onCreated: () => void | Promise<void>;
  onError: (message: string) => void;
}) {
  const [text, setText] = useState("");
  const [type, setType] = useState<QuestionType>("multiple_choice");
  const [options, setOptions] = useState<string[]>(["", "", "", ""]);
  const [correct, setCorrect] = useState("0");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text) return;
    try {
      await api.createQuestion(reportId, {
        text,
        type,
        options: type === "multiple_choice" ? options : ["Verdadero", "Falso"],
        correct_answer: correct,
        limit_seconds: limitSeconds,
      });
      await onCreated();
      onClose();
    } catch (err: any) {
      onError(err.message || "Error al crear pregunta");
    }
  };

  return (
    <ModalFrame className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-fg">Agregar Pregunta Personalizada al Pool</h3>
        <button type="button" onClick={onClose} className="text-muted hover:text-fg">
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
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
          <Select value={type} onChange={(e) => setType(e.target.value as QuestionType)}>
            <option value="multiple_choice">Selección Múltiple (4 alternativas)</option>
            <option value="true_false">Verdadero / Falso</option>
          </Select>
        </Field>

        {type === "multiple_choice" && (
          <div className="space-y-2">
            <span className="block font-bold text-fg">Alternativas y Respuesta Correcta</span>
            {options.map((opt, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="font-bold text-muted">{String.fromCharCode(65 + i)})</span>
                <Input
                  density="sm"
                  fill={false}
                  className="flex-1"
                  type="text"
                  required
                  placeholder={`Opción ${String.fromCharCode(65 + i)}`}
                  value={opt}
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
                  className="h-4 w-4 accent-brand"
                  title="Marcar como correcta"
                />
              </div>
            ))}
          </div>
        )}

        {type === "true_false" && (
          <div className="flex gap-4">
            {[
              { value: "0", label: "Verdadero es la correcta" },
              { value: "1", label: "Falso es la correcta" },
            ].map((option) => (
              <label key={option.value} className={cx("flex items-center gap-2 text-fg")}>
                <input
                  type="radio"
                  name="correct-tf"
                  className="accent-brand"
                  checked={correct === option.value}
                  onChange={() => setCorrect(option.value)}
                />
                {option.label}
              </label>
            ))}
          </div>
        )}

        <Button type="submit" className="w-full rounded-control py-2.5 font-bold">
          Guardar Pregunta
        </Button>
      </form>
    </ModalFrame>
  );
}
