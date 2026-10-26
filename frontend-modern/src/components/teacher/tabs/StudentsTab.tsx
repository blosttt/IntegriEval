"use client";

import type { FormEvent } from "react";
import { Plus, Trash2, Upload, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboard, usePersistentState } from "../DashboardContext";
import {
  Button,
  DataTable,
  EmptyNote,
  FileInput,
  Hint,
  Input,
  Panel,
  ReadOnlyNote,
  SectionTitle,
} from "../ui";

export default function StudentsTab() {
  const {
    isAssistant,
    students,
    setStudents,
    selectedCourseId,
    setError,
    setSuccess,
    setStudentToEdit,
  } = useDashboard();
  const [name, setName] = usePersistentState("students.name", "");
  const [email, setEmail] = usePersistentState("students.email", "");
  const [csvFile, setCsvFile] = usePersistentState<File | null>("students.csvFile", null);
  const [csvImporting, setCsvImporting] = usePersistentState("students.csvImporting", false);

  const reloadRoster = async () => {
    if (selectedCourseId) setStudents(await api.getStudents(selectedCourseId));
  };

  const createStudent = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;
    setError("");
    setSuccess("");
    try {
      await api.createStudent(selectedCourseId, { name, email });
      setSuccess("Estudiante agregado correctamente.");
      setName("");
      setEmail("");
      await reloadRoster();
    } catch (err: any) {
      setError(err.message || "Error al agregar estudiante");
    }
  };

  const importCsv = async (e: FormEvent) => {
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
      await reloadRoster();
    } catch (err: any) {
      setError(err.message || "Error al importar CSV");
    } finally {
      setCsvImporting(false);
    }
  };

  const deleteStudent = async (studentId: number) => {
    if (!selectedCourseId || !confirm("¿Retirar este estudiante de la nómina activa del curso?")) return;
    try {
      await api.deleteStudent(selectedCourseId, studentId);
      setSuccess("Estudiante eliminado.");
      await reloadRoster();
    } catch (err: any) {
      setError(err.message || "Error al eliminar");
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      {!isAssistant && (
        <div className="space-y-6">
          <Panel>
            <SectionTitle icon={Upload}>Cargar Lista CSV</SectionTitle>
            <Hint>
              Carga un archivo CSV con columnas <b>Nombre</b> y <b>Correo</b>. Los alumnos no requieren
              crearse cuenta.
            </Hint>
            <form data-tour="csv-import" onSubmit={importCsv} className="space-y-3">
              <FileInput
                accept=".csv"
                required
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
              />
              <Button type="submit" size="block" disabled={csvImporting || !csvFile}>
                {csvImporting ? "Importando..." : "Importar Estudiantes"}
              </Button>
            </form>
          </Panel>

          <Panel>
            <SectionTitle icon={Plus}>Agregar Individual</SectionTitle>
            <form onSubmit={createStudent} className="space-y-3">
              <Input
                type="text"
                required
                placeholder="Nombre Completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <Input
                type="email"
                required
                placeholder="estudiante@universidad.cl"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <Button type="submit" variant="secondary" size="block">
                Agregar Estudiante
              </Button>
            </form>
          </Panel>
        </div>
      )}

      {isAssistant && (
        <ReadOnlyNote>
          Puedes consultar los alumnos del curso. Agregar, importar, editar o retirar alumnos corresponde
          al profesor y al superadministrador.
        </ReadOnlyNote>
      )}

      <Panel className={isAssistant ? "md:col-span-3" : "md:col-span-2"}>
        <div className="flex items-center justify-between">
          <SectionTitle icon={Users} data-tour="student-roster">
            Nómina del Curso ({students.length})
          </SectionTitle>
        </div>

        {students.length === 0 ? (
          <EmptyNote>
            {isAssistant
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
                  {!isAssistant && (
                    <>
                      <Button variant="link" className="mr-3 text-xs" onClick={() => setStudentToEdit(s)}>
                        Editar
                      </Button>
                      <Button
                        variant="danger"
                        className="p-1"
                        title="Retirar estudiante"
                        onClick={() => deleteStudent(s.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </>
                  )}
                  {isAssistant && (
                    <span className="text-xs leading-[1.65] text-muted">Solo lectura</span>
                  )}
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Panel>
    </div>
  );
}
