"use client";

import React, { useState } from "react";
import { Eye, FileUp, HelpCircle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import MarkdownPreviewModal from "../MarkdownPreviewModal";
import {
  Button, DataTable, EmptyNote, FileInput, Hint, Panel, Select, SectionTitle, btnPill, cx, panelClass,
} from "../ui";

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  pending: { label: "Pendiente", className: "bg-line text-muted" },
  processing: { label: "Analizando...", className: "animate-pulse bg-yellow-950/60 text-yellow-400" },
  completed: { label: "Completado", className: "bg-emerald-950/60 text-emerald-400" },
  error: { label: "Error", className: "bg-red-950/60 text-red-400" },
};

export default function ReportsTab() {
  const {
    students, selectedEvalId, selectedEval, reports, loadEvalSubData, openReportQuestions,
    setError, setSuccess, setActiveTab,
  } = useDashboard();

  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkMapping, setBulkMapping] = useState<{ [filename: string]: number }>({});
  const [bulkUploading, setBulkUploading] = useState(false);
  const [markdown, setMarkdown] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);

  const handleFilesSelect = (files: FileList | null) => {
    if (!files) return;
    const fileArr = Array.from(files);
    setBulkFiles(fileArr);

    const mapping: { [key: string]: number } = {};
    fileArr.forEach((file) => {
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

  const handleBulkUpload = async () => {
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
      setSuccess("¡Trabajos subidos! Los informes fueron extraídos y analizados.");
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

  const handleReanalyze = async (reportId: number) => {
    try {
      await api.reanalyzeReport(reportId);
      setSuccess("Reanálisis iniciado.");
      if (selectedEvalId) loadEvalSubData(selectedEvalId);
    } catch (err: any) {
      setError(err.message || "Error al reanalizar");
    }
  };

  const handlePreviewMarkdown = async (reportId: number) => {
    try {
      const data = await api.getReportMarkdown(reportId);
      setMarkdown(data.markdown || "Sin contenido Markdown extraído.");
      setPreviewOpen(true);
    } catch (err: any) {
      setError("No se pudo cargar el Markdown");
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
            data-tour="report-upload"
            className="w-full sm:w-auto"
            onChange={(e) => handleFilesSelect(e.target.files)}
          />
          {bulkFiles.length > 0 && (
            <Button
              variant="success"
              onClick={handleBulkUpload}
              disabled={bulkUploading}
              className="w-full rounded-control px-6 py-2.5 text-xs font-bold sm:w-auto"
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
                    setBulkMapping((prev) => ({ ...prev, [file.name]: Number(e.target.value) }))
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

      <details key={selectedEvalId} className={panelClass}>
        <summary className="cursor-pointer text-sm font-bold uppercase tracking-wider text-fg">
          Análisis IA · {selectedEval?.title} ({reports.length} trabajos)
        </summary>
        <Button
          variant="ghost"
          className="gap-1 text-xs"
          onClick={() => selectedEvalId && loadEvalSubData(selectedEvalId)}
        >
          <RefreshCw className="h-3.5 w-3.5" /> Actualizar
        </Button>

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
              const badge = STATUS_BADGES[r.analysis_status];
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
                    {badge && (
                      <span className={cx("rounded px-2 py-0.5", badge.className)}>{badge.label}</span>
                    )}
                  </td>
                  <td className="py-3 font-semibold text-fg">{scorePct != null ? `${scorePct}%` : "--"}</td>
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
                      variant="ghost"
                      className="p-1"
                      onClick={() => handlePreviewMarkdown(r.id)}
                      title="Ver Markdown extraído"
                    >
                      <Eye className="inline h-4 w-4" />
                    </Button>
                    <Button className={btnPill} onClick={() => openReportQuestions(r)}>
                      <HelpCircle className="h-3 w-3" /> Pool Preguntas
                    </Button>
                    <Button
                      variant="ghost"
                      className="p-1"
                      onClick={() => handleReanalyze(r.id)}
                      title="Reanalizar con IA"
                    >
                      <RefreshCw className="inline h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              );
            })}
          </DataTable>
        )}
      </details>

      {previewOpen && <MarkdownPreviewModal markdown={markdown} onClose={() => setPreviewOpen(false)} />}
    </div>
  );
}
