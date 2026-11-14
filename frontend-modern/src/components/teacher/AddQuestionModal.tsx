"use client";

import { useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "./DashboardContext";
import { Banner, Button, Field, Input, ModalFrame, Select, Textarea } from "./ui";

export default function AddQuestionModal({ onClose, onSave, question, criteriaNames }: {
  onClose: () => void;
  onSave?: (data: any) => Promise<void>;
  question?: any;
  criteriaNames?: string[];
}) {
  const [criterion, setCriterion] = useState<string>(question?.seccion_origen || "");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState('');
  const { selectedReportId, selectedEval, setSuccess, setError, setQuestionBank } = useDashboard();
  const draftKey = (field: string) => onSave ? null : "question." + field;
  const [text, setText] = usePersistentState(draftKey("text"), question?.text ?? "");
  const [type, setType] = usePersistentState<"multiple_choice" | "true_false" | "open_ended">(
    draftKey("type"),
    question?.type ?? "multiple_choice",
  );
  const [options, setOptions] = usePersistentState<string[]>(draftKey("options"), question?.options ?? ["", "", "", ""]);
  const [correct, setCorrect] = usePersistentState(draftKey("correct"), question?.correct_answer ?? "0");
  const [reference, setReference] = usePersistentState(draftKey("reference"), question?.reference_answer ?? "");
  const [criteria, setCriteria] = usePersistentState(draftKey("criteria"), question?.grading_criteria ?? "");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if ((!selectedReportId && !onSave) || !text || busy) return;
    setBusy(true);
    setLocalError('');
    try {
      const data = {
        text,
        type,
        seccion_origen: criterion || null,
        options: type === "multiple_choice" ? options : type === "true_false" ? ["Verdadero", "Falso"] : [],
        reference_answer: reference,
        grading_criteria: criteria,
        correct_answer: correct,
        limit_seconds: selectedEval?.time_per_question || 30,
      };
      if (onSave) await onSave(data);
      else {
        await api.createQuestion(selectedReportId!, data);
        setQuestionBank(await api.getQuestionBank(selectedReportId!));
      }
      setSuccess(question ? "Pregunta actualizada." : "Pregunta agregada al pool.");
      onClose();
      setText("");
      setOptions(["", "", "", ""]);
      setCorrect("0");
      setReference("");
      setCriteria("");
    } catch (err: any) {
      setLocalError(err.message || 'No se pudo crear la pregunta');
      setError(err.message || "Error al crear pregunta");
    } finally { setBusy(false); }
  };

  return (
    <ModalFrame className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-fg">{question ? "Editar pregunta del pool general" : onSave ? "Agregar pregunta al pool general" : "Agregar Pregunta Personalizada al Pool"}</h3>
        <Button variant="muted" disabled={busy} onClick={onClose}>
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
          <Select value={type} onChange={(e) => {
            const next = e.target.value as "multiple_choice" | "true_false" | "open_ended";
            if (next === "multiple_choice" && options.length < 4) setOptions(["", "", "", ""]);
            setCorrect("0");
            setType(next);
          }}>
            <option value="multiple_choice">Selección Múltiple (4 alternativas)</option>
            <option value="true_false">Verdadero / Falso</option>
            <option value="open_ended">Desarrollo (respuesta escrita)</option>
          </Select>
        </Field>

        {!!criteriaNames?.length && <Field label="Criterio de la rúbrica">
          <Select value={criterion} onChange={e => setCriterion(e.target.value)}>
            <option value="">Sin criterio asignado</option>
            {criteriaNames.map(name => <option key={name}>{name}</option>)}
          </Select>
        </Field>}

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

        {type === "open_ended" && <div className="space-y-3">
          <Field label="Criterios de evaluación (solo docente)">
            <Textarea rows={3} required maxLength={10000} value={criteria} onChange={e => setCriteria(e.target.value)} placeholder="Qué debe explicar el estudiante y cómo se asignará el puntaje." />
          </Field>
          <Field label="Respuesta de referencia (opcional, solo docente)">
            <Textarea rows={3} maxLength={10000} value={reference} onChange={e => setReference(e.target.value)} />
          </Field>
          <p className="text-xs text-muted">El estudiante escribirá su respuesta. La corrección será manual, de 0 a 100 puntos. Cada pregunta tiene el mismo peso. Revisa que el tiempo por pregunta de la evaluación sea suficiente.</p>
        </div>}

        {localError && <Banner tone="error" role="alert">{localError}</Banner>}
        <Button type="submit" disabled={busy} size="block" className="py-2.5">
          {busy ? 'Guardando…' : 'Guardar Pregunta'}
        </Button>
      </form>
    </ModalFrame>
  );
}
