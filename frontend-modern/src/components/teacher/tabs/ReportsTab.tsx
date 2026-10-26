"use client";

import type { ReactNode } from "react";
import { Eye, FileUp, HelpCircle, RefreshCw } from "lucide-react";
import UploadQueue from "@/components/UploadQueue";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "../DashboardContext";
import {
  Button,
  DataTable,
  EmptyNote,
  FileInput,
  Hint,
  Panel,
  SectionTitle,
  Select,
  panelClasses,
} from "../ui";

const STATUS_BADGES: Record<string, ReactNode> = {
  pending: <span className="rounded bg-raised px-2 py-0.5 text-muted">Pendiente</span>,
  processing: (
    <span className="animate-pulse rounded bg-yellow-950/60 px-2 py-0.5 text-yellow-400">Analizando...</span>
  ),
  completed: <span className="rounded bg-emerald-950/60 px-2 py-0.5 text-emerald-400">Completado</span>,
  error: <span className="rounded bg-red-950/60 px-2 py-0.5 text-red-400">Error</span>,
};

export default function ReportsTab() {
  const {
    students,
    reports,
    selectedCourseId,
    selectedEvalId,
    selectedEval,
    loadEvalSubData,
    setError,
    setSuccess,
    setActiveTab,
    setSelectedReport,
    setSelectedReportId,
    setQuestionBank,
    setSelectedQIds,
    setReportMarkdown,
    setPreviewMdModal,
  } = useDashboard();
  const [bulkFiles, setBulkFiles] = usePersistentState<File[]>("reports.bulkFiles", []);
  const [bulkMapping, setBulkMapping] = usePersistentState<Record<string, number>>(
    "reports.bulkMapping",
    {},
  );
  const [bulkUploading, setBulkUploading] = usePersistentState("reports.bulkUploading", false);

  const selectFiles = (files: FileList | null) => {
    if (!files) return;
    const list = Array.from(files);
    setBulkFiles(list);
    const mapping: Record<string, number> = {};
    list.forEach((file) => {
      const lower = file.name.toLowerCase();
      const match = students.find(
        (s) =>
          lower.includes(s.name.toLowerCase().split(" ")[0]) ||
          lower.includes(s.email.split("@")[0].toLowerCase()),
      );
      if (match) mapping[file.name] = match.id;
    });
    setBulkMapping(mapping);
  };

  const executeBulkUpload = async () => {
    if (!selectedEvalId || bulkFiles.length === 0) return;
    const unmapped = bulkFiles.filter((f) => !bulkMapping[f.name]);
    if (unmapped.length > 0) {
      setError(`Falta asociar ${unmapped.length} archivo(s) a un estudiante.`);
      return;
    }
    const studentIds = bulkFiles.map((f) => bulkMapping[f.name]);
    setError("");
    setSuccess("");
    setBulkUploading(true);
    try {
      await api.bulkUploadReports(selectedEvalId, studentIds, bulkFiles);
      setSuccess("Archivos en cola. Puedes seguir el avance y reintentar errores individualmente.");
      setBulkFiles([]);
      setBulkMapping({});
      await loadEvalSubData(selectedEvalId);
      setActiveTab("reports");
    } catch (err: any) {
      setError(err.message || "Error en la subida en lote");
    } finally {
      setBulkUploading(false);
    }
  };

  const reanalyze = async (reportId: number) => {
    try {
      await api.reanalyzeReport(reportId);
      setSuccess("Reanálisis iniciado.");
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al reanalizar");
    }
  };

  const previewMarkdown = async (reportId: number) => {
    try {
      const data = await api.getReportMarkdown(reportId);
      setReportMarkdown(data.markdown || "Sin contenido Markdown extraído.");
      setPreviewMdModal(true);
    } catch (err: any) {
      setError("No se pudo cargar el Markdown");
    }
  };

  const openQuestions = async (report: any) => {
    setSelectedReport(report);
    setSelectedReportId(report.id);
    setActiveTab("questions");
    try {
      const bank = await api.getQuestionBank(report.id);
      setQuestionBank(bank);
      setSelectedQIds(bank.selected_question_ids || []);
    } catch (err: any) {
      setError(err.message || "Banco de preguntas no disponible aún.");
      setQuestionBank(null);
    }
  };

  return (
    <div className="space-y-6">
      <Panel size="lg">
        <SectionTitle icon={FileUp}>Subida en Lote de Trabajos de Estudiantes</SectionTitle>
        <Hint>
          Selecciona todos los PDFs descargados de la plataforma de la universidad. El sistema detectará
          automáticamente el estudiante correspondiente o puedes mapearlo manualmente.
        </Hint>

        <div className="flex flex-col items-center gap-4 sm:flex-row">
          <FileInput
            large
            multiple
            accept=".pdf,.md,.txt,.markdown"
            className="w-full sm:w-auto"
            data-tour="report-upload"
            onChange={(e) => selectFiles(e.target.files)}
          />
          {bulkFiles.length > 0 && (
            <Button
              variant="success"
              className="w-full rounded-control px-6 py-2.5 text-xs font-bold sm:w-auto"
              onClick={executeBulkUpload}
              disabled={bulkUploading}
            >
              {bulkUploading ? "Analizando Trabajos con IA..." : `Procesar ${bulkFiles.length} Trabajos`}
            </Button>
          )}
        </div>

        {bulkFiles.length > 0 && (
          <div className="mt-4 max-h-60 space-y-2 overflow-y-auto border-t border-line pt-4">
            <h4 className="text-xs font-bold text-fg">Asociación de Archivos:</h4>
            {bulkFiles.map((file) => (
              <div
                key={file.name}
                className="flex flex-col items-start justify-between gap-2 rounded-lg bg-raised p-2 text-xs sm:flex-row sm:items-center"
              >
                <span className="max-w-sm truncate font-mono text-fg">{file.name}</span>
                <Select
                  density="xs"
                  fill={false}
                  value={bulkMapping[file.name] || ""}
                  onChange={(e) =>
                    setBulkMapping((previous) => ({ ...previous, [file.name]: Number(e.target.value) }))
                  }
                >
                  <option value="">-- Seleccionar Estudiante --</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.email})
                    </option>
                  ))}
                </Select>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {selectedCourseId && selectedEvalId && (
        <UploadQueue
          courseId={selectedCourseId}
          evaluationId={selectedEvalId}
          onCompleted={() => loadEvalSubData(selectedEvalId)}
        />
      )}

      <details key={selectedEvalId} className={panelClasses("lg")}>
        <summary className="cursor-pointer text-sm font-bold tracking-wider text-fg uppercase">
          Análisis IA · {selectedEval?.title} ({reports.length} trabajos)
        </summary>
        <div>
          <Button
            variant="muted"
            className="gap-1 text-xs"
            onClick={() => selectedEvalId && loadEvalSubData(selectedEvalId)}
          >
            <RefreshCw className="h-3.5 w-3.5" /> Actualizar
          </Button>
        </div>

        {reports.length === 0 ? (
          <EmptyNote>No hay trabajos subidos para esta evaluación.</EmptyNote>
        ) : (
          <DataTable
            columns={[
              "Estudiante",
              "Estado Análisis",
              "Nota Preliminar IA",
              "Detección IA",
              "Flash Test",
              { label: "Acciones", align: "right" },
            ]}
          >
            {reports.map((r) => {
              const aiPct =
                r.ai_detected_percentage != null ? Math.round(r.ai_detected_percentage * 100) : null;
              const scorePct =
                r.final_score_percentage != null
                  ? Math.round(r.final_score_percentage * 100)
                  : r.ai_score_percentage != null
                    ? Math.round(r.ai_score_percentage * 100)
                    : null;
              return (
                <tr key={r.id}>
                  <td className="py-3">
                    <div className="font-bold text-fg">{r.student_name}</div>
                    <div className="text-[10px] text-muted">{r.student_email}</div>
                  </td>
                  <td className="py-3">
                    {STATUS_BADGES[r.analysis_status] || null}
                    <p className="text-xs text-muted">
                      {r.analysis_engine}
                      {r.analysis_fallback ? " · respaldo simulado" : ""}
                    </p>
                    {r.analysis_status === "error" && <p className="text-xs text-red-400">Análisis incompleto. Reintenta; cualquier nota anterior es histórica.</p>}
                    {r.evaluacion?.desglose?.cobertura_documento && <p className="text-xs text-muted">
                      {r.evaluacion.desglose.cobertura_documento.caracteres_originales.toLocaleString("es-CL")} caracteres · {r.evaluacion.desglose.cobertura_documento.estrategia === "sintesis_por_secciones"
                        ? `${r.evaluacion.desglose.cobertura_documento.secciones_originales} secciones sintetizadas`
                        : "texto completo"}
                    </p>}
                  </td>
                  <td className="py-3 font-semibold text-fg">
                    {scorePct != null ? `${scorePct}%` : "--"}
                  </td>
                  <td className="py-3">
                    {aiPct != null ? (
                      <span className={aiPct > 40 ? "font-bold text-red-400" : "text-fg"}>
                        {aiPct}% {aiPct > 40 && "⚠️"}
                      </span>
                    ) : (
                      "--"
                    )}
                  </td>
                  <td className="py-3">
                    {r.flash_completed ? (
                      <span className="font-bold text-emerald-400">Rendido</span>
                    ) : r.flash_email_sent ? (
                      <span className="text-brand-ink">Correo Enviado</span>
                    ) : (
                      <span className="text-muted">No enviado</span>
                    )}
                  </td>
                  <td className="space-x-2 py-3 text-right">
                    <Button
                      variant="muted"
                      className="p-1"
                      title="Ver Markdown extraído"
                      onClick={() => previewMarkdown(r.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button size="pill" onClick={() => openQuestions(r)}>
                      <HelpCircle className="h-3 w-3" /> Pool Preguntas
                    </Button>
                    <Button
                      variant="muted"
                      className="p-1"
                      title="Reanalizar con IA"
                      onClick={() => reanalyze(r.id)}
                    >
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              );
            })}
          </DataTable>
        )}
      </details>
    </div>
  );
}
