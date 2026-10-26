"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  Pencil,
  UserMinus,
  Users,
  BookOpen,
  GraduationCap,
  ShieldCheck,
  ArrowUpRight,
} from "lucide-react";
import Link from "next/link";
import Navbar from "./Navbar";
import Dialog from "./Dialog";
import StudentEditor from "./StudentEditor";
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
  MutedText,
  PageHeading,
  buttonClasses,
  courseRowClasses,
  shellClasses,
  surfacePanelClasses,
  workspaceClasses,
} from "./ui";

const sectionHeading =
  "mb-[22px] flex items-center justify-between gap-[15px] max-[720px]:flex-wrap max-[720px]:items-start";
const panelTitle = "text-[17px] font-semibold";
const countChip = "rounded-[5px] bg-raised px-1.5 py-[3px] text-[11px] font-normal text-muted";
const th =
  "border-b border-line px-3 py-3.5 text-left text-[11px] font-semibold tracking-[0.04em] text-muted uppercase";
const td = "border-b border-line px-3 py-4 align-middle text-fg";
const rowActions = "flex items-center gap-4 [&_button]:px-2.5 [&_button]:py-[7px] [&_button]:text-[11px]";

export default function AdminManagement() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState("courses");
  const [courses, setCourses] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [assigned, setAssigned] = useState<any[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [editor, setEditor] = useState<any>(null);
  const [studentEditor, setStudentEditor] = useState<any>(null);
  const [confirm, setConfirm] = useState<any>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [cs, ts] = await Promise.all([api.getCourses(), request("/admin/profesores")]);
    setCourses(cs);
    setTeachers(ts);
    setCourseId((current) => (cs.some((c: any) => c.id === current) ? current : cs[0]?.id || null));
  };

  const loadCourse = async () => {
    if (!courseId) {
      setStudents([]);
      setAssigned([]);
      return;
    }
    const [ss, tt] = await Promise.all([
      api.getStudents(courseId),
      request(`/admin/asignaturas/${courseId}/profesores`),
    ]);
    setStudents(ss);
    setAssigned(tt);
  };

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
      .catch(() => router.replace("/login"));
  }, []);

  useEffect(() => {
    if (ready) loadCourse().catch((e) => setError(e.message));
  }, [courseId, ready]);

  const run = async (action: () => Promise<any>, message: string) => {
    setError("");
    setBusy(true);
    try {
      await action();
      setNotice(message);
      await load();
      await loadCourse();
      return true;
    } catch (e: any) {
      setError(e.message);
      return false;
    } finally {
      setBusy(false);
    }
  };

  const open = (kind: string, data?: any) => {
    setError("");
    setEditor({ kind, data });
  };

  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const values: any = Object.fromEntries(new FormData(event.currentTarget));
    let path = "";
    let method = "POST";
    const body: any = values;
    if (editor.kind === "teacher") {
      path = "/admin/profesores" + (editor.data ? "/" + editor.data.id : "");
      method = editor.data ? "PUT" : "POST";
      body.active = values.active === "true";
      if (!body.contrasena) delete body.contrasena;
    } else {
      path = "/asignaturas" + (editor.data ? "/" + editor.data.id : "");
      method = editor.data ? "PUT" : "POST";
      body.ano = Number(body.ano);
    }
    if (
      await run(
        () => request(path, method, body),
        editor.kind === "teacher" ? "Profesor guardado" : "Asignatura guardada",
      )
    )
      setEditor(null);
  };

  const assignTeacher = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await run(
      () =>
        request(`/admin/asignaturas/${courseId}/profesores`, "POST", {
          usuario_id: Number(form.get("teacher")),
        }),
      "Profesor asignado al curso",
    );
  };

  if (!ready)
    return (
      <div className={shellClasses}>
        <Navbar />
        <p className="my-20 text-center text-muted">Verificando acceso de administrador…</p>
      </div>
    );

  const selected = courses.find((c) => c.id === courseId);
  const tabs: any[] = [
    ["courses", "Asignaturas", BookOpen],
    ["teachers", "Profesores", GraduationCap],
    ["students", "Estudiantes", Users],
  ];

  return (
    <div className={shellClasses}>
      <Navbar />
      <main className={workspaceClasses("max-w-[1240px]")}>
        <PageHeading
          eyebrow={
            <>
              <ShieldCheck size={16} />
              Administración académica
            </>
          }
          title="Personas y asignaturas"
          description="Crea los cursos, asigna a sus profesores y administra la nómina de cada asignatura."
        >
          <Link className={buttonClasses("surface", "classic")} href="/admin/audit">
            Ver auditoría
            <ArrowUpRight size={16} />
          </Link>
        </PageHeading>
        <nav
          className="mb-7 flex gap-2 overflow-x-auto border-b border-line"
          aria-label="Gestión administrativa"
        >
          {tabs.map(([key, label, Icon]) => (
            <button
              key={key}
              className={`flex cursor-pointer items-center gap-2 border-b-2 px-5 py-3.5 text-[13px] whitespace-nowrap ${
                tab === key ? "border-brand text-[#84c9f4]" : "border-transparent text-muted"
              }`}
              onClick={() => {
                setTab(key);
                setError("");
              }}
            >
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
        {error && !editor && !confirm && (
          <Banner tone="error" role="alert">
            {error}
          </Banner>
        )}
        {notice && (
          <Banner tone="success" role="status">
            {notice}
          </Banner>
        )}
        {tab === "courses" && (
          <div className="grid grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)] gap-6 max-[1000px]:grid-cols-1">
            <section className={surfacePanelClasses}>
              <div className={sectionHeading}>
                <h2 className={panelTitle}>
                  Asignaturas <span className={countChip}>{courses.length}</span>
                </h2>
                <Button size="classic" onClick={() => open("course")}>
                  <Plus size={16} />
                  Crear asignatura
                </Button>
              </div>
              {!courses.length ? (
                <EmptyState>Crea la primera asignatura para comenzar.</EmptyState>
              ) : (
                <div className="flex flex-col gap-3">
                  {courses.map((c) => (
                    <div className={courseRowClasses(c.id === courseId)} key={c.id}>
                      <button
                        className="flex min-w-0 flex-1 cursor-pointer flex-col gap-2 text-left text-fg"
                        onClick={() => setCourseId(c.id)}
                      >
                        <strong className="text-sm font-semibold">{c.name}</strong>
                        <span className="text-xs text-muted">
                          {c.period} · {c.ano} · {c.student_count || 0} estudiantes
                        </span>
                      </button>
                      <div className="flex items-center gap-4">
                        <IconButton aria-label={`Editar ${c.name}`} onClick={() => open("course", c)}>
                          <Pencil size={16} />
                        </IconButton>
                        <IconButton
                          danger
                          aria-label={`Archivar ${c.name}`}
                          onClick={() =>
                            setConfirm({
                              title: "Archivar asignatura",
                              text: "Se retirará de los cursos activos. Se conservarán sus evaluaciones y auditoría.",
                              action: () => request(`/admin/asignaturas/${c.id}`, "DELETE"),
                              message: "Asignatura archivada",
                            })
                          }
                        >
                          <UserMinus size={16} />
                        </IconButton>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
            <section className={surfacePanelClasses}>
              <h2 className={panelTitle}>Profesores del curso</h2>
              <MutedText>{selected?.name || "Selecciona una asignatura"}</MutedText>
              {courseId && (
                <>
                  <div className="my-5">
                    {assigned.length ? (
                      assigned.map((t) => (
                        <div
                          key={t.id}
                          className="flex items-center justify-between gap-3 border-b border-line py-3.5"
                        >
                          <span>
                            <strong className="text-sm">{t.nombre}</strong>
                            <small className="mt-1 block text-xs text-muted">
                              {t.correo}
                              {!t.active ? " · Desactivado" : ""}
                            </small>
                          </span>
                          <Button
                            variant="dangerSoft"
                            size="classic"
                            onClick={() =>
                              setConfirm({
                                title: "Retirar profesor del curso",
                                text: `${t.nombre} perderá el acceso a esta asignatura. Sus registros históricos se conservarán.`,
                                action: () =>
                                  request(`/admin/asignaturas/${courseId}/profesores/${t.id}`, "DELETE"),
                                message: "Acceso del profesor retirado",
                              })
                            }
                          >
                            Retirar
                          </Button>
                        </div>
                      ))
                    ) : (
                      <EmptyState>Todavía no hay docentes asignados.</EmptyState>
                    )}
                  </div>
                  <form
                    className="my-5 flex items-end gap-2.5 max-[720px]:flex-wrap"
                    onSubmit={assignTeacher}
                  >
                    <FormField label="Asignar profesor" className="min-w-0 flex-1 max-[720px]:basis-full">
                      <FormSelect name="teacher" required defaultValue="">
                        <option value="" disabled>
                          Seleccionar profesor activo…
                        </option>
                        {teachers
                          .filter((t) => t.active && !assigned.some((a) => a.id === t.id))
                          .map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.nombre} · {t.correo}
                            </option>
                          ))}
                      </FormSelect>
                    </FormField>
                    <Button type="submit" size="classic" disabled={busy}>
                      Asignar
                    </Button>
                  </form>
                  <MutedText>
                    Cada docente podrá editar alumnos, materiales y evaluaciones únicamente dentro de
                    sus cursos.
                  </MutedText>
                </>
              )}
            </section>
          </div>
        )}
        {tab === "teachers" && (
          <section className={surfacePanelClasses}>
            <div className={sectionHeading}>
              <h2 className={panelTitle}>
                Profesores <span className={countChip}>{teachers.length}</span>
              </h2>
              <Button size="classic" onClick={() => open("teacher")}>
                <Plus size={16} />
                Agregar profesor
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    <th className={th}>Profesor</th>
                    <th className={th}>Correo</th>
                    <th className={th}>Estado</th>
                    <th className={th}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {teachers.map((t) => (
                    <tr key={t.id}>
                      <td className={td}>{t.nombre}</td>
                      <td className={td}>{t.correo}</td>
                      <td className={td}>
                        <Badge tone={t.active ? "teacher" : "inactive"}>
                          {t.active ? "Activo" : "Desactivado"}
                        </Badge>
                      </td>
                      <td className={td}>
                        <div className={rowActions}>
                          <Button variant="surface" size="classic" onClick={() => open("teacher", t)}>
                            <Pencil size={15} />
                            Editar
                          </Button>
                          {t.active && (
                            <Button
                              variant="dangerSoft"
                              size="classic"
                              onClick={() =>
                                setConfirm({
                                  title: "Desactivar profesor",
                                  text: `${t.nombre} no podrá iniciar sesión ni utilizar sus accesos actuales. Se conservará su historial.`,
                                  action: () => request(`/admin/profesores/${t.id}`, "DELETE"),
                                  message: "Profesor desactivado",
                                })
                              }
                            >
                              Desactivar
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!teachers.length && <EmptyState>Agrega el primer profesor.</EmptyState>}
            </div>
          </section>
        )}
        {tab === "students" && (
          <section className={surfacePanelClasses}>
            <div className={sectionHeading}>
              <div>
                <h2 className={panelTitle}>Estudiantes del curso</h2>
                <FormField label="Asignatura" className="mt-[18px] min-w-[260px]">
                  <FormSelect
                    value={courseId || ""}
                    onChange={(e) => setCourseId(Number(e.target.value))}
                  >
                    {courses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} · {c.period}
                      </option>
                    ))}
                  </FormSelect>
                </FormField>
              </div>
              <Button size="classic" disabled={!courseId} onClick={() => setStudentEditor({})}>
                <Plus size={16} />
                Agregar estudiante
              </Button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-[13px]">
                <thead>
                  <tr>
                    <th className={th}>Nombre</th>
                    <th className={th}>Correo</th>
                    <th className={th}>RUT</th>
                    <th className={th}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td className={td}>{s.name}</td>
                      <td className={td}>{s.email}</td>
                      <td className={td}>{s.rut || "—"}</td>
                      <td className={td}>
                        <div className={rowActions}>
                          <Button variant="surface" size="classic" onClick={() => setStudentEditor(s)}>
                            Editar
                          </Button>
                          <Button
                            variant="dangerSoft"
                            size="classic"
                            onClick={() =>
                              setConfirm({
                                title: "Retirar estudiante del curso",
                                text: `${s.name} dejará de figurar en la nómina activa y sus tests pendientes quedarán inhabilitados. Se conservará el historial.`,
                                action: () => api.deleteStudent(courseId!, s.id),
                                message: "Estudiante retirado de la nómina activa",
                              })
                            }
                          >
                            Retirar
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!students.length && <EmptyState>Esta asignatura todavía no tiene estudiantes.</EmptyState>}
            </div>
          </section>
        )}
        {editor && (
          <Dialog
            title={`${editor.data ? "Editar" : "Agregar"} ${editor.kind === "teacher" ? "profesor" : "asignatura"}`}
            onClose={() => setEditor(null)}
          >
            <form onSubmit={save}>
              <FormStack>
                {error && (
                  <Banner tone="error" role="alert">
                    {error}
                  </Banner>
                )}
                <FormField label={editor.kind === "teacher" ? "Nombre completo" : "Nombre de la asignatura"}>
                  <FormInput
                    name="nombre"
                    defaultValue={editor.data?.nombre || editor.data?.name || ""}
                    required
                    maxLength={120}
                  />
                </FormField>
                {editor.kind === "teacher" ? (
                  <>
                    <FormField label="Correo institucional">
                      <FormInput
                        type="email"
                        name="correo"
                        defaultValue={editor.data?.correo || ""}
                        required
                      />
                    </FormField>
                    <FormField
                      label={editor.data ? "Nueva contraseña (dejar vacía para conservar)" : "Contraseña inicial"}
                    >
                      <FormInput
                        type="password"
                        autoComplete="new-password"
                        name="contrasena"
                        minLength={6}
                        required={!editor.data}
                      />
                    </FormField>
                    <FormField label="Estado">
                      <FormSelect name="active" defaultValue={editor.data?.active === false ? "false" : "true"}>
                        <option value="true">Activo</option>
                        <option value="false">Desactivado</option>
                      </FormSelect>
                    </FormField>
                  </>
                ) : (
                  <>
                    <FormField label="Período">
                      <FormInput
                        name="periodo"
                        defaultValue={editor.data?.period || "Semestre 2"}
                        required
                        maxLength={50}
                      />
                    </FormField>
                    <FormField label="Año">
                      <FormInput
                        type="number"
                        name="ano"
                        min={2000}
                        max={2200}
                        defaultValue={editor.data?.ano || new Date().getFullYear()}
                        required
                      />
                    </FormField>
                  </>
                )}
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
        {studentEditor && courseId && (
          <StudentEditor
            courseId={courseId}
            student={studentEditor.id ? studentEditor : undefined}
            onClose={() => setStudentEditor(null)}
            onSaved={() => {
              loadCourse();
              load();
              setNotice("Estudiante guardado");
            }}
          />
        )}
        {confirm && (
          <Dialog title={confirm.title} onClose={() => setConfirm(null)}>
            <FormStack>
              <p>{confirm.text}</p>
              {error && (
                <Banner tone="error" role="alert">
                  {error}
                </Banner>
              )}
            </FormStack>
            <DialogFooter>
              <Button variant="surface" size="classic" onClick={() => setConfirm(null)}>
                Cancelar
              </Button>
              <Button
                size="classic"
                disabled={busy}
                onClick={async () => {
                  if (await run(confirm.action, confirm.message)) setConfirm(null);
                }}
              >
                Confirmar
              </Button>
            </DialogFooter>
          </Dialog>
        )}
      </main>
    </div>
  );
}
