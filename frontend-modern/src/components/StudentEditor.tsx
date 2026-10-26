"use client";

import { useState, type FormEvent } from "react";
import Dialog from "./Dialog";
import { request } from "@/lib/api";
import {
  Banner,
  Button,
  DialogFooter,
  FormField,
  FormInput,
  FormStack,
  MutedText,
} from "./ui";

export default function StudentEditor({
  courseId,
  student,
  onClose,
  onSaved,
}: {
  courseId: number;
  student?: any;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await request(
        `/asignaturas/${courseId}/estudiantes${student ? "/" + student.id : ""}`,
        student ? "PUT" : "POST",
        data,
      );
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog title={student ? "Editar estudiante" : "Agregar estudiante"} onClose={onClose}>
      <form onSubmit={submit}>
        <FormStack>
          {error && (
            <Banner tone="error" role="alert">
              {error}
            </Banner>
          )}
          <FormField label="Nombre completo">
            <FormInput
              name="nombre"
              defaultValue={student?.nombre || student?.name || ""}
              required
              maxLength={150}
            />
          </FormField>
          <FormField label="Correo institucional">
            <FormInput
              name="correo"
              type="email"
              defaultValue={student?.correo || student?.email || ""}
              required
            />
          </FormField>
          <FormField label="RUT (opcional)">
            <FormInput name="rut" defaultValue={student?.rut || ""} maxLength={20} />
          </FormField>
          <MutedText>
            El estudiante accederá únicamente al Flash Test mediante su enlace personal, sin crear
            una cuenta.
          </MutedText>
        </FormStack>
        <DialogFooter>
          <Button variant="surface" size="classic" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" size="classic" disabled={busy}>
            {busy ? "Guardando…" : "Guardar estudiante"}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
