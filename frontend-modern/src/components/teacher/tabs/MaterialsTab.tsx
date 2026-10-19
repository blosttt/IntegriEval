"use client";

import React, { useState } from "react";
import { BookOpen, Trash2, Upload } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import { Button, EmptyNote, FileInput, Hint, Input, Panel, SectionTitle, btnBlock } from "../ui";

export default function MaterialsTab() {
  const { selectedEvalId, materials, setMaterials, setError, setSuccess } = useDashboard();

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvalId || !file || !title) return;
    setError("");
    setSuccess("");
    setUploading(true);
    try {
      await api.uploadMaterial(selectedEvalId, title, file);
      setSuccess("Material de apoyo subido y convertido a Markdown para el contexto IA.");
      setTitle("");
      setFile(null);
      setMaterials(await api.getMaterials(selectedEvalId));
    } catch (err: any) {
      setError(err.message || "Error al subir material");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (matId: number) => {
    if (!selectedEvalId || !confirm("¿Eliminar este material?")) return;
    try {
      await api.deleteMaterial(selectedEvalId, matId);
      setSuccess("Material eliminado.");
      setMaterials(await api.getMaterials(selectedEvalId));
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <Panel>
        <SectionTitle icon={Upload}>Subir Material del Curso</SectionTitle>
        <Hint>
          Sube syllabus, guías o bibliografía en PDF, Markdown o TXT. La IA los convertirá a Markdown y los
          usará como base de conocimiento para evaluar con justicia y precisión.
        </Hint>

        <form data-tour="material-upload" onSubmit={handleUpload} className="space-y-3">
          <Input
            type="text"
            required
            placeholder="Título, ej. Guía de Metodología y Rúbrica"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <FileInput
            accept=".pdf,.md,.txt,.markdown"
            required
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <Button type="submit" disabled={uploading} className={btnBlock}>
            {uploading ? "Procesando PDF a Markdown..." : "Subir y Analizar Material"}
          </Button>
        </form>
      </Panel>

      <Panel className="md:col-span-2">
        <SectionTitle icon={BookOpen}>Materiales de Apoyo Activos ({materials.length})</SectionTitle>
        {materials.length === 0 ? (
          <EmptyNote>No has subido documentos de apoyo para esta evaluación.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {materials.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-control border border-line bg-raised p-3.5 text-xs"
              >
                <div>
                  <h4 className="font-bold text-fg">{m.title}</h4>
                  <p className="mt-0.5 text-[10px] text-muted">
                    Subido el {new Date(m.uploaded_at).toLocaleDateString("es-CL")}
                  </p>
                </div>
                <Button
                  variant="danger"
                  className="p-1.5"
                  onClick={() => handleDelete(m.id)}
                  title="Eliminar material"
                >
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
