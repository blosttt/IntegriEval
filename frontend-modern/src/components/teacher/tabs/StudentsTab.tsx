"use client";

import React, { useState } from "react";
import { Plus, Trash2, Upload, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard } from "../DashboardContext";
import {
  Button, DataTable, EmptyNote, FileInput, Hint, Input, Panel, ReadOnlyNote, SectionTitle,
  btnBlock, cx,
} from "../ui";

export default function StudentsTab() {
  const {
    accountRole, students, selectedCourseId, setError, setSuccess, refreshStudents, setStudentToEdit,
  } = useDashboard();

  const [newStudentName, setNewStudentName] = useState("");
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvImporting, setCsvImporting] = useState(false);

  const readOnly = accountRole === "ayudante";

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      await api.createStudent(selectedCourseId, { name: newStudentName, email: newStudentEmail });
      setSuccess("Estudiante agregado correctamente.");
      setNewStudentName("");
      setNewStudentEmail("");
      await refreshStudents();
    } catch (err: any) {
      setError(err.message || "Error al agregar estudiante");
    }
  };

  const handleImportCSV = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !csvFile) return;
    setError("");
    setSuccess("");
    setCsvImporting(true);
    try {
      const res = await api.importStudentsCSV(selectedCourseId, csvFile);
      setSuccess(`Importación lista: ${res.created} agregados, ${res.skipped} ya existían.`);
      if (res.errores?.length) setError(res.errores.join("; "));
      setCsvFile(null);
      await refreshStudents();
    } catch (err: any) {
      setError(err.message || "Error al importar CSV");
    } finally {
      setCsvImporting(false);
    }
  };

  const handleDeleteStudent = async (studentId: number) => {
    if (!selectedCourseId || !confirm("¿Retirar este estudiante de la nómina activa del curso?")) return;
    try {
      await api.deleteStudent(selectedCourseId, studentId);
      setSuccess("Estudiante eliminado.");
      await refreshStudents();
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      {!readOnly && (
        <div className="space-y-6">
          <Panel>
            <SectionTitle icon={Upload}>Cargar Lista CSV</SectionTitle>
            <Hint>
              Carga un archivo CSV con columnas <b>Nombre</b> y <b>Correo</b>. Los alumnos no requieren
              crearse cuenta.
            </Hint>
            <form data-tour="csv-import" onSubmit={handleImportCSV} className="space-y-3">
              <FileInput
                accept=".csv"
                required
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
              />
              <Button type="submit" disabled={csvImporting || !csvFile} className={btnBlock}>
                {csvImporting ? "Importando..." : "Importar Estudiantes"}
              </Button>
            </form>
          </Panel>

          <Panel>
            <SectionTitle icon={Plus}>Agregar Individual</SectionTitle>
            <form onSubmit={handleCreateStudent} className="space-y-3">
              <Input
                type="text"
                required
                placeholder="Nombre Completo"
                value={newStudentName}
                onChange={(e) => setNewStudentName(e.target.value)}
              />
              <Input
                type="email"
                required
                placeholder="estudiante@universidad.cl"
                value={newStudentEmail}
                onChange={(e) => setNewStudentEmail(e.target.value)}
              />
              <Button type="submit" variant="secondary" className={btnBlock}>
                Agregar Estudiante
              </Button>
            </form>
          </Panel>
        </div>
      )}

      {readOnly && (
        <ReadOnlyNote>
          Puedes consultar los alumnos del curso. Agregar, importar, editar o retirar alumnos corresponde al
          profesor y al superadministrador.
        </ReadOnlyNote>
      )}

      <Panel className={cx(readOnly ? "md:col-span-3" : "md:col-span-2")}>
        <div className="flex items-center justify-between">
          <SectionTitle icon={Users} data-tour="student-roster">
            Nómina del Curso ({students.length})
          </SectionTitle>
        </div>

        {students.length === 0 ? (
          <EmptyNote>
            {readOnly
              ? "El curso todavía no tiene alumnos. El profesor o el superadministrador debe cargar la nómina."
              : "No hay estudiantes registrados en este curso. Sube un CSV o agrégalos manualmente."}
          </EmptyNote>
        ) : (
          <DataTable
            headPadding="pb-2"
            columns={["ID", "Nombre", "Correo", { label: "Acción", align: "right" }]}
          >
            {students.map((s) => (
              <tr key={s.id}>
                <td className="py-2.5 font-mono text-muted">{s.id}</td>
                <td className="py-2.5 font-semibold text-fg">{s.name}</td>
                <td className="py-2.5 text-muted">{s.email}</td>
                <td className="py-2.5 text-right">
                  {!readOnly && (
                    <>
                      <button
                        type="button"
                        className="mr-3 text-xs text-brand-ink"
                        onClick={() => setStudentToEdit(s)}
                      >
                        Editar
                      </button>
                      <Button
                        variant="danger"
                        className="p-1"
                        onClick={() => handleDeleteStudent(s.id)}
                        title="Retirar estudiante"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </>
                  )}
                  {readOnly && <span className="text-muted">Solo lectura</span>}
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Panel>
    </div>
  );
}
