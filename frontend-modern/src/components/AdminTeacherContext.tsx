"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { ArrowLeft, ShieldCheck, Plus, Pencil, UserMinus } from "lucide-react";
import Dialog from "./Dialog";
import { request } from "@/lib/api";
import {
  Banner,
  Button,
  DialogFooter,
  FormField,
  FormInput,
  FormSelect,
  FormStack,
  MutedText,
  courseRowClasses,
} from "./ui";

export default function AdminTeacherContext({
  person,
  courses,
  onChanged,
}: {
  person: any;
  courses: any[];
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [editor, setEditor] = useState<any>(null);
  const [allCourses, setAllCourses] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [remove, setRemove] = useState<any>(null);

  const manage = async () => {
    setOpen(true);
    setError("");
    try {
      setAllCourses(await request("/asignaturas"));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const d: any = Object.fromEntries(new FormData(e.currentTarget));
    d.ano = Number(d.ano);
    try {
      await request(
        editor.id ? `/asignaturas/${editor.id}` : `/admin/profesores/${person.id}/asignaturas`,
        editor.id ? "PUT" : "POST",
        d,
      );
      setEditor(null);
      setOpen(false);
      onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const assignExisting = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const id = String(new FormData(e.currentTarget).get("course"));
    try {
      await request(`/admin/asignaturas/${id}/profesores`, "POST", { usuario_id: person.id });
      setOpen(false);
      onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const confirmRemove = async () => {
    setBusy(true);
    try {
      await request(`/admin/asignaturas/${remove.id}/profesores/${person.id}`, "DELETE");
      setRemove(null);
      setOpen(false);
      onChanged();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <aside className="flex items-center justify-between gap-5 rounded-lg border border-[#148bd04d] bg-[#148bd00b] px-[21px] py-[18px] text-fg max-[700px]:flex-col max-[700px]:items-start">
        <div>
          <Link
            href="/admin/dashboard"
            className="mb-3 inline-flex items-center gap-1.5 text-[11px] text-[#75c5f1]"
          >
            <ArrowLeft size={16} />
            Volver a Super admin
          </Link>
          <strong className="flex items-center gap-2 text-[17px] font-semibold">
            <ShieldCheck size={17} />
            Vista de {person.nombre}
          </strong>
          <p className="mt-2 text-xs leading-[1.6] text-muted">
            Actúas como superadministrador. Puedes modificar este espacio; la auditoría conserva tu
            identidad.
          </p>
        </div>
        <Button variant="surface" size="classic" onClick={manage}>
          Gestionar asignaturas
        </Button>
      </aside>
      {open && !editor && !remove && (
        <Dialog title={`Asignaturas de ${person.nombre}`} onClose={() => setOpen(false)} wide>
          <FormStack>
            {error && (
              <Banner tone="error" role="alert">
                {error}
              </Banner>
            )}
            {courses.length ? (
              <div className="flex flex-col gap-3">
                {courses.map((c) => (
                  <div className={courseRowClasses()} key={c.id}>
                    <span>
                      <strong>{c.name}</strong>
                      <MutedText>
                        {c.period} · {c.ano}
                      </MutedText>
                    </span>
                    <div className="flex items-center gap-4">
                      <Button
                        variant="surface"
                        size="classic"
                        onClick={() => {
                          setEditor(c);
                          setError("");
                        }}
                      >
                        <Pencil size={15} />
                        Editar
                      </Button>
                      <Button variant="dangerSoft" size="classic" onClick={() => setRemove(c)}>
                        <UserMinus size={15} />
                        Retirar acceso
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>Este docente todavía no tiene asignaturas.</p>
            )}
            <Button
              size="classic"
              onClick={() => {
                setEditor({});
                setError("");
              }}
            >
              <Plus size={16} />
              Crear y asignar una asignatura
            </Button>
            <form className="my-5 flex items-end gap-2.5 max-[720px]:flex-wrap" onSubmit={assignExisting}>
              <FormField label="Asignar una existente" className="min-w-0 flex-1 max-[720px]:basis-full">
                <FormSelect name="course" required defaultValue="">
                  <option value="" disabled>
                    Selecciona una asignatura…
                  </option>
                  {allCourses
                    .filter((c) => !courses.some((assigned) => assigned.id === c.id))
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre} · {c.periodo}
                      </option>
                    ))}
                </FormSelect>
              </FormField>
              <Button type="submit" variant="surface" size="classic" disabled={busy}>
                Asignar
              </Button>
            </form>
          </FormStack>
        </Dialog>
      )}
      {editor && (
        <Dialog
          title={editor.id ? "Editar asignatura" : "Crear y asignar asignatura"}
          onClose={() => setEditor(null)}
        >
          <form onSubmit={save}>
            <FormStack>
              {error && (
                <Banner tone="error" role="alert">
                  {error}
                </Banner>
              )}
              <FormField label="Nombre">
                <FormInput name="nombre" defaultValue={editor.name || ""} maxLength={150} required />
              </FormField>
              <FormField label="Período">
                <FormInput
                  name="periodo"
                  defaultValue={editor.period || "Semestre 2"}
                  maxLength={50}
                  required
                />
              </FormField>
              <FormField label="Año">
                <FormInput
                  name="ano"
                  type="number"
                  min={2000}
                  max={2200}
                  defaultValue={editor.ano || new Date().getFullYear()}
                  required
                />
              </FormField>
            </FormStack>
            <DialogFooter>
              <Button variant="surface" size="classic" onClick={() => setEditor(null)}>
                Cancelar
              </Button>
              <Button type="submit" size="classic" disabled={busy}>
                {busy ? "Guardando…" : "Guardar"}
              </Button>
            </DialogFooter>
          </form>
        </Dialog>
      )}
      {remove && (
        <Dialog title="Retirar acceso a la asignatura" onClose={() => setRemove(null)}>
          <FormStack>
            <p>
              {person.nombre} perderá el acceso a {remove.name}. Los datos del curso se conservarán.
            </p>
            {error && <Banner tone="error">{error}</Banner>}
          </FormStack>
          <DialogFooter>
            <Button variant="surface" size="classic" onClick={() => setRemove(null)}>
              Cancelar
            </Button>
            <Button size="classic" disabled={busy} onClick={confirmRemove}>
              Retirar acceso
            </Button>
          </DialogFooter>
        </Dialog>
      )}
    </>
  );
}
