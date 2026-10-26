"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Search, Plus, ArrowRight, Pencil, ShieldCheck, GraduationCap, Users } from "lucide-react";
import IntegrationStatus from "./IntegrationStatus";
import GmailSettings from "./GmailSettings";
import Navbar from "./Navbar";
import Dialog from "./Dialog";
import { api, request } from "@/lib/api";
import {
  Badge,
  Banner,
  Button,
  DialogFooter,
  EmptyState,
  FormField,
  FormInput,
  FormSelect,
  FormStack,
  IconButton,
  PageHeading,
  buttonClasses,
  shellClasses,
  workspaceClasses,
} from "./ui";

export default function SuperAdmin() {
  const router = useRouter();
  const [people, setPeople] = useState<any[]>([]);
  const [ready, setReady] = useState(false);
  const [query, setQuery] = useState("");
  const [editor, setEditor] = useState<any>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => setPeople(await request("/admin/profesores"));

  useEffect(() => {
    api
      .getMe()
      .then((u) => {
        if (u.rol !== "admin") {
          router.replace("/");
          return;
        }
        setReady(true);
        load().catch((e) => setError(e.message));
      })
      .catch(() => router.replace("/#acceso"));
  }, []);

  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data: any = Object.fromEntries(new FormData(e.currentTarget));
    data.active = data.active === "true";
    if (!data.contrasena) delete data.contrasena;
    try {
      await request(
        "/admin/profesores" + (editor.id ? "/" + editor.id : ""),
        editor.id ? "PUT" : "POST",
        data,
      );
      await load();
      setEditor(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const visible = people.filter((p) =>
    `${p.nombre} ${p.correo}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className={shellClasses}>
      <Navbar />
      <main className={workspaceClasses("max-w-[1240px]")}>
        <PageHeading
          eyebrow={
            <>
              <ShieldCheck size={16} />
              Super admin
            </>
          }
          title="Selecciona un docente"
          description="Abre su espacio de trabajo para revisar y administrar sus cursos con tus permisos de superadministrador."
        >
          <Button
            size="classic"
            onClick={() => {
              setEditor({});
              setError("");
            }}
          >
            <Plus size={16} />
            Agregar docente
          </Button>
        </PageHeading>
        {!ready ? (
          <EmptyState>Verificando acceso…</EmptyState>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <IntegrationStatus />
              <GmailSettings />
            </div>
            <label className="mb-7 flex max-w-[700px] items-center gap-3 rounded-[7px] border border-line bg-surface px-4 py-[13px] text-muted">
              <Search size={18} />
              <input
                className="min-w-0 flex-1 bg-transparent text-[13px] text-fg outline-none"
                aria-label="Buscar profesor o ayudante"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar por nombre o correo"
              />
              <span className="text-[11px] whitespace-nowrap max-[700px]:hidden">
                {visible.length} docentes
              </span>
            </label>
            {error && !editor && (
              <Banner tone="error" role="alert">
                {error}
              </Banner>
            )}
            <div className="grid grid-cols-3 gap-5 max-[1000px]:grid-cols-2 max-[700px]:grid-cols-1">
              {visible.map((person) => (
                <article
                  className="flex flex-col rounded-[10px] border border-line bg-surface p-[23px] transition-[border-color] duration-150 hover:border-[#148bd080]"
                  key={person.id}
                >
                  <div className="mb-[22px] flex items-center justify-between">
                    <span className="grid size-12 place-items-center rounded-[10px] border border-[#148bd026] bg-[#148bd014] text-[#75c5f1]">
                      {person.rol === "ayudante" ? <Users size={24} /> : <GraduationCap size={24} />}
                    </span>
                    <Badge tone={person.active ? "teacher" : "inactive"}>
                      {person.active ? "Activo" : "Desactivado"}
                    </Badge>
                  </div>
                  <h2 className="text-lg leading-[1.4] font-semibold text-fg">
                    <Link href={`/teacher/dashboard?profesor=${person.id}`}>{person.nombre}</Link>
                  </h2>
                  <p className="mt-2 mb-[18px] text-xs [overflow-wrap:anywhere] text-muted">
                    {person.correo}
                  </p>
                  <div className="flex justify-between gap-3 pb-[22px] text-[11px] text-muted">
                    <span>{person.rol === "ayudante" ? "Ayudante" : "Profesor"}</span>
                    <span>{person.asignaturas.length} asignaturas</span>
                  </div>
                  <footer className="mt-auto flex items-center justify-between gap-3 border-t border-line pt-[18px]">
                    <Link
                      className={buttonClasses("primary", "classic", "flex-1")}
                      href={`/teacher/dashboard?profesor=${person.id}`}
                    >
                      Abrir vista
                      <ArrowRight size={16} />
                    </Link>
                    <IconButton
                      aria-label={`Editar cuenta de ${person.nombre}`}
                      onClick={() => {
                        setEditor(person);
                        setError("");
                      }}
                    >
                      <Pencil size={17} />
                    </IconButton>
                  </footer>
                </article>
              ))}
            </div>
            {!visible.length && (
              <EmptyState>
                {people.length
                  ? "No se encontraron docentes con esa búsqueda."
                  : "Agrega el primer profesor o ayudante para comenzar."}
              </EmptyState>
            )}
          </>
        )}
        {editor && (
          <Dialog
            title={editor.id ? "Editar cuenta docente" : "Agregar profesor o ayudante"}
            onClose={() => setEditor(null)}
          >
            <form onSubmit={save}>
              <FormStack>
                {error && (
                  <Banner tone="error" role="alert">
                    {error}
                  </Banner>
                )}
                <FormField label="Nombre completo">
                  <FormInput name="nombre" defaultValue={editor.nombre || ""} required maxLength={120} />
                </FormField>
                <FormField label="Correo institucional">
                  <FormInput name="correo" type="email" defaultValue={editor.correo || ""} required />
                </FormField>
                <FormField label="Perfil">
                  <FormSelect name="rol" defaultValue={editor.rol || "docente"} disabled={!!editor.id}>
                    <option value="docente">Profesor</option>
                    <option value="ayudante">Ayudante · sin edición de alumnos</option>
                  </FormSelect>
                </FormField>
                <FormField label={editor.id ? "Nueva contraseña (opcional)" : "Contraseña inicial"}>
                  <FormInput
                    name="contrasena"
                    type="password"
                    autoComplete="new-password"
                    minLength={6}
                    required={!editor.id}
                  />
                </FormField>
                <FormField label="Estado">
                  <FormSelect name="active" defaultValue={editor.active === false ? "false" : "true"}>
                    <option value="true">Activo</option>
                    <option value="false">Desactivado</option>
                  </FormSelect>
                </FormField>
              </FormStack>
              <DialogFooter>
                <Button variant="surface" size="classic" onClick={() => setEditor(null)}>
                  Cancelar
                </Button>
                <Button type="submit" size="classic" disabled={busy}>
                  {busy ? "Guardando…" : "Guardar cuenta"}
                </Button>
              </DialogFooter>
            </form>
          </Dialog>
        )}
      </main>
    </div>
  );
}
