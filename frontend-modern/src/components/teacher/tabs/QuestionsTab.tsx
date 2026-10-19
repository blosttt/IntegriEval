"use client";

import { useState } from "react";
import { Check, Edit, Mail, Plus, Sparkles, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import AddQuestionModal from "../AddQuestionModal";
import { Button, Panel, btnToolbar, cx } from "../ui";

export default function QuestionsTab() {
  const {
    selectedReport, selectedReportId, selectedEval, selectedEvalId, questionBank, setQuestionBank,
    selectedQIds, setSelectedQIds, setError, setSuccess, setFlashLink, loadEvalSubData,
  } = useDashboard();

  const [showAddModal, setShowAddModal] = useState(false);
  const flashCount = selectedEval?.flash_questions_count || 10;

  const reloadBank = async () => {
    if (selectedReportId) setQuestionBank(await api.getQuestionBank(selectedReportId));
  };

  const toggleQuestion = (qId: number) =>
    setSelectedQIds((prev) => (prev.includes(qId) ? prev.filter((id) => id !== qId) : [...prev, qId]));

  const handleSelectRandom = async () => {
    if (!selectedReportId) return;
    try {
      const updatedBank = await api.selectRandomQuestions(selectedReportId);
      setQuestionBank(updatedBank);
      setSelectedQIds(updatedBank.selected_question_ids || []);
      setSuccess("Preguntas seleccionadas aleatoriamente.");
    } catch (err: any) {
      setError(err.message || "Error al seleccionar aleatoriamente");
    }
  };

  const handleSendFlashTest = async () => {
    if (!selectedReportId) return;
    if (selectedQIds.length === 0) {
      setError("Debes seleccionar al menos una pregunta antes de enviar.");
      return;
    }
    setError("");
    try {
      await api.selectQuestions(selectedReportId, selectedQIds);
      const dispatch = await api.sendFlashTest(selectedReportId);
      const item = dispatch.items?.[0];
      if (!item) {
        setError("El test ya fue completado o no hay preguntas seleccionadas.");
        return;
      }
      setSuccess(
        item.correo_enviado
          ? "Correo enviado con el enlace de verificación."
          : "Enlace disponible. SMTP no envió correo.",
      );
      setFlashLink(item.enlace_test);
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
      await reloadBank();
    } catch (err: any) {
      setError(err.message || "Error al enviar el Flash Test");
    }
  };

  const handleEditQuestion = async (question: any) => {
    const text = window.prompt("Enunciado de la pregunta:", question.text);
    if (!text) return;
    const raw = window.prompt("Alternativas (lista JSON):", JSON.stringify(question.options));
    if (!raw) return;
    const answer = window.prompt(
      "Letra de la alternativa correcta:",
      String.fromCharCode(65 + Number(question.correct_answer)),
    );
    if (!answer) return;
    try {
      const options = JSON.parse(raw);
      if (!Array.isArray(options) || options.some((v) => typeof v !== "string"))
        throw new Error("Indique una lista de textos");
      await api.updateQuestion(selectedReportId!, question.id, {
        text,
        options,
        correct_answer: String(answer.trim().toUpperCase().charCodeAt(0) - 65),
      });
      await reloadBank();
      setSuccess("Pregunta actualizada");
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteQuestion = async (qId: number) => {
    if (!selectedReportId || !confirm("¿Eliminar pregunta del pool?")) return;
    try {
      await api.deleteQuestion(selectedReportId, qId);
      setSuccess("Pregunta eliminada.");
      await reloadBank();
      setSelectedQIds((prev) => prev.filter((id) => id !== qId));
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  return (
    <div className="space-y-6">
      <Panel
        size="lg"
        stack={false}
        className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center"
      >
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-ink">
            Estudiante: {selectedReport?.student_name}
          </span>
          <h2 data-tour="questions-pool" className="mt-0.5 text-lg font-bold text-fg">
            Pool de Preguntas Flash ({questionBank?.questions?.length || 0} disponibles)
          </h2>
          <p className="text-xs text-muted">
            Selecciona las {flashCount} preguntas que se enviarán al estudiante por correo. Puedes editarlas
            o agregar preguntas propias.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" className={btnToolbar} onClick={handleSelectRandom}>
            <Sparkles className="h-3.5 w-3.5 text-brand-ink" />
            Selección Aleatoria ({flashCount})
          </Button>
          <Button variant="outline" className={btnToolbar} onClick={() => setShowAddModal(true)}>
            <Plus className="h-3.5 w-3.5" />
            Agregar Pregunta Propia
          </Button>
          <Button
            data-tour="flash-dispatch"
            className="rounded-control px-5 py-2 text-xs font-bold shadow-lg"
            onClick={handleSendFlashTest}
            disabled={selectedQIds.length === 0}
          >
            <Mail className="h-3.5 w-3.5" />
            Aprobar y Enviar Flash Test ({selectedQIds.length})
          </Button>
        </div>
      </Panel>

      {!questionBank || questionBank.questions.length === 0 ? (
        <Panel size="xl" className="text-center text-xs text-muted">
          El banco de preguntas aún no ha sido generado para este informe. Espera que termine el análisis.
        </Panel>
      ) : (
        <div className="space-y-3">
          {questionBank.questions.map((q: any, idx: number) => {
            const isSelected = selectedQIds.includes(q.id);
            return (
              <div
                key={q.id}
                className={cx(
                  "rounded-control border p-4 transition-all",
                  isSelected ? "border-brand bg-brand-soft" : "border-line bg-surface",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleQuestion(q.id)}
                      className="mt-1 h-4 w-4 cursor-pointer rounded accent-brand"
                    />
                    <div>
                      <span className="mr-2 text-[10px] font-bold uppercase text-muted">
                        #{idx + 1} {q.is_custom && "• Creada por Profesor"}
                      </span>
                      <p className="mt-0.5 text-sm font-semibold text-fg">{q.text}</p>

                      {q.options && (
                        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                          {q.options.map((opt: string, oIdx: number) => {
                            const isCorrect = String(oIdx) === String(q.correct_answer);
                            return (
                              <div
                                key={oIdx}
                                className={cx(
                                  "flex items-center justify-between rounded-lg border p-2 text-xs",
                                  isCorrect
                                    ? "border-emerald-500/30 bg-emerald-950/40 font-semibold text-emerald-300"
                                    : "border-line bg-raised text-muted",
                                )}
                              >
                                <span>
                                  {String.fromCharCode(65 + oIdx)}. {opt}
                                </span>
                                {isCorrect && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="link"
                    className="p-1"
                    title="Editar pregunta"
                    onClick={() => handleEditQuestion(q)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <button
                    type="button"
                    onClick={() => handleDeleteQuestion(q.id)}
                    className="p-1 text-muted hover:text-red-400"
                    title="Eliminar del pool"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showAddModal && selectedReportId && (
        <AddQuestionModal
          reportId={selectedReportId}
          limitSeconds={selectedEval?.time_per_question || 30}
          onClose={() => setShowAddModal(false)}
          onError={setError}
          onCreated={async () => {
            setSuccess("Pregunta agregada al pool.");
            await reloadBank();
          }}
        />
      )}
    </div>
  );
}
