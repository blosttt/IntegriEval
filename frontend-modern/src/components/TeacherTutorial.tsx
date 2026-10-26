"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, X, Check } from "lucide-react";
import { api } from "@/lib/api";
import { Button, IconButton } from "./ui";

const baseSteps = [
  {tab:'courses',target:'course-selector',title:'1. Selecciona tu asignatura',text:'Este selector determina con qué curso estás trabajando. Solo aparecen las asignaturas que te asignó el superadministrador. El resto de la página pertenece al curso seleccionado.'},
  {tab:'students',target:'student-roster',title:'2. Revisa los alumnos del curso',text:'Aquí está la nómina. Revisa nombres y correos antes de evaluar: el enlace personal del Flash Test se enviará a ese correo.'},
  {tab:'students',target:'csv-import',title:'3. Carga o actualiza la nómina',text:'Puedes importar un CSV con nombre y correo. Los duplicados se omiten y los errores se informan. También puedes agregar alumnos y editar sus datos desde la tabla.',teacherOnly:true},
  {tab:'evaluations',target:'rubric',title:'4. Escribe la pauta de evaluación',text:'Explica qué esperas del informe: contenidos, criterios y evidencias. Esta pauta contextualiza el análisis y las preguntas de verificación.'},
  {tab:'evaluations',target:'question-settings',title:'5. Ajusta las preguntas y el tiempo',text:'Define el tamaño del pool y cuántas preguntas verá el estudiante. Revisa el rigor, el tiempo por pregunta y los umbrales. Guarda los parámetros al terminar.'},
  {tab:'materials',target:'material-upload',title:'6. Añade material de apoyo',text:'Sube syllabus, guías o bibliografía en PDF, Markdown o TXT. Este contexto acompaña la pauta al evaluar el informe.'},
  {tab:'reports',target:'report-upload',title:'7. Carga los informes PDF',text:'Selecciona los informes y comprueba a qué alumno corresponde cada archivo antes de procesarlos. Después podrás consultar el texto extraído y abrir el pool de preguntas. Con el motor mock, el análisis es de demostración.'},
  {tab:'questions',target:'questions-pool',title:'8. Revisa el pool de preguntas',text:'Desde un informe analizado, abre «Pool Preguntas». En esta sección revisas, editas o agregas preguntas y marcas cuáles se utilizarán. Si todavía no hay informes, el pool aparecerá después de procesar el primero.'},
  {tab:'questions',target:'flash-dispatch',title:'9. Aprueba y despacha el Flash Test',text:'Este botón genera el enlace personal del alumno con las preguntas seleccionadas. El alumno no inicia sesión. Si SMTP está configurado, recibe el enlace por correo; de lo contrario, se muestra aquí para compartirlo.'},
  {tab:'results',target:'results',title:'10. Revisa y confirma los resultados',text:'Contrasta el logro del informe con las respuestas del Flash Test. Al confirmar o ajustar el logro debes registrar una justificación. Puedes agendar una defensa cuando necesites verificar la comprensión.'},
  {tab:'appointments',target:'appointments',title:'11. Registra la defensa y sus acuerdos',text:'Aquí revisas las citas agendadas y registras su estado, acuerdos y ajustes justificados. La evaluación final la determina el docente, no el indicador de IA.'}
];

type Box = { top: number; left: number; width: number; height: number };

export default function TeacherTutorial({
  onStep,
  assistant = false,
}: {
  onStep: (tab: any) => void;
  assistant?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const [key, setKey] = useState("");
  const [box, setBox] = useState<Box | null>(null);
  const [viewport, setViewport] = useState({ width: 1000, height: 800 });
  const tip = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const stepCallback = useRef(onStep);
  stepCallback.current = onStep;

  const steps = useMemo(
    () =>
      baseSteps
        .filter((step) => !assistant || !step.teacherOnly)
        .map((step) =>
          assistant && step.target === "student-roster"
            ? {
                ...step,
                text: "Puedes consultar la nómina y los correos de este curso. Como ayudante no puedes agregar, importar, editar ni retirar alumnos. El resto del flujo de evaluación está habilitado.",
              }
            : step,
        ),
    [assistant],
  );

  useEffect(() => {
    let alive = true;
    api
      .getMe()
      .then((user) => {
        if (!alive || !["docente", "ayudante"].includes(user.rol)) return;
        const k = `integryeval:walkthrough:v2:${user.id}`;
        setKey(k);
        if (!localStorage.getItem(k)) {
          previousFocus.current = document.activeElement as HTMLElement;
          setIndex(0);
          setOpen(true);
        }
      })
      .catch(() => {});
    const start = () => {
      previousFocus.current = document.activeElement as HTMLElement;
      setIndex(0);
      setOpen(true);
    };
    window.addEventListener("integryeval:open-tutorial", start);
    return () => {
      alive = false;
      window.removeEventListener("integryeval:open-tutorial", start);
    };
  }, []);

  const close = () => {
    if (key) localStorage.setItem(key, "seen");
    setOpen(false);
    setBox(null);
    previousFocus.current?.focus();
  };

  useEffect(() => {
    if (!open) return;
    stepCallback.current(steps[index].tab);
    setBox(null);
    let frame = 0;
    let attempt = 0;
    let element: HTMLElement | null = null;
    let resize: ResizeObserver | null = null;
    const measure = () => {
      if (!element) return;
      const r = element.getBoundingClientRect();
      const w = window.innerWidth;
      const h = window.innerHeight;
      const top = Math.max(8, r.top - 7);
      const left = Math.max(8, r.left - 7);
      const right = Math.min(w - 8, r.right + 7);
      const bottom = Math.min(h - 8, r.bottom + 7);
      setViewport({ width: w, height: h });
      const next = {
        top,
        left,
        width: Math.max(0, right - left),
        height: Math.max(0, bottom - top),
      };
      setBox((old) =>
        old &&
        Math.abs(old.top - next.top) < 1 &&
        Math.abs(old.left - next.left) < 1 &&
        Math.abs(old.width - next.width) < 1 &&
        Math.abs(old.height - next.height) < 1
          ? old
          : next,
      );
    };
    const locate = () => {
      element = document.querySelector<HTMLElement>(`[data-tour="${steps[index].target}"]`);
      if (!element && attempt++ < 90) {
        frame = requestAnimationFrame(locate);
        return;
      }
      if (!element)
        element = document.querySelector<HTMLElement>(`[data-tour="tab-${steps[index].tab}"]`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
        resize = new ResizeObserver(measure);
        resize.observe(element);
        measure();
      }
    };
    frame = requestAnimationFrame(locate);
    window.addEventListener("scroll", measure, true);
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(frame);
      resize?.disconnect();
      window.removeEventListener("scroll", measure, true);
      window.removeEventListener("resize", measure);
    };
  }, [open, index, steps]);

  useEffect(() => {
    if (!open) return;
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [open, key]);

  useEffect(() => {
    if (open && box) tip.current?.focus({ preventScroll: true });
  }, [open, index, !!box]);

  if (!open) return null;

  const width = Math.min(366, viewport.width - 32);
  const height = tip.current?.offsetHeight || 300;
  let left = (viewport.width - width) / 2;
  let top = viewport.height - height - 20;
  if (box) {
    if (box.left + box.width + width + 28 < viewport.width) {
      left = box.left + box.width + 16;
      top = box.top;
    } else if (box.left - width - 24 > 0) {
      left = box.left - width - 16;
      top = box.top;
    } else {
      left = Math.max(16, Math.min(box.left, viewport.width - width - 16));
      top =
        box.top + box.height + height + 24 < viewport.height
          ? box.top + box.height + 16
          : box.top - height - 16;
    }
  }
  top = Math.max(16, Math.min(top, viewport.height - height - 16));

  const last = index === steps.length - 1;

  return (
    <>
      {box && box.width > 0 && box.height > 0 && (
        <div
          className="pointer-events-none fixed z-[8000] rounded-lg border-2 border-[#54b9f1] shadow-[0_0_0_9999px_#000b,0_0_0_5px_#148bd040] transition-[top,left,width,height] duration-150"
          data-testid="tour-highlight"
          aria-hidden="true"
          style={{ top: box.top, left: box.left, width: box.width, height: box.height }}
        />
      )}
      <div
        ref={tip}
        role="dialog"
        aria-modal="false"
        aria-labelledby="walkthrough-title"
        tabIndex={-1}
        className="fixed z-[8001] max-h-[calc(100dvh-32px)] overflow-auto rounded-[10px] border border-[#148bd080] bg-surface px-5 pt-[17px] pb-[18px] font-ui text-fg shadow-[0_18px_70px_#0009] outline-none max-[700px]:px-[17px] max-[700px]:py-[15px]"
        style={{ top, left, width }}
        data-testid="tour-tooltip"
      >
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] font-semibold tracking-[0.05em] text-[#75c5f1] uppercase">
            Guía de uso · {index + 1} / {steps.length}
          </span>
          <IconButton onClick={close} aria-label="Cerrar guía">
            <X size={17} />
          </IconButton>
        </div>
        <div
          className="mx-0 mt-[9px] mb-[19px] flex gap-1"
          aria-label={`Paso ${index + 1} de ${steps.length}`}
        >
          {steps.map((s, i) => (
            <span
              key={s.target}
              className={`h-1 flex-1 rounded ${i <= index ? "bg-brand" : "bg-line"}`}
            />
          ))}
        </div>
        <h2
          id="walkthrough-title"
          className="mb-3 text-[19px] leading-[1.35] font-[650] tracking-[-0.3px] max-[700px]:text-lg"
        >
          {steps[index].title.replace(/^\d+\. /, "")}
        </h2>
        <p className="text-[13px] leading-[1.75] text-muted max-[700px]:text-xs">
          {steps[index].text}
        </p>
        <span className="mt-4 block rounded-[5px] bg-[#148bd00d] px-3 py-[11px] text-[11px] leading-[1.6] text-muted">
          Puedes interactuar con el elemento destacado. La guía no modifica datos por ti.
        </span>
        <footer className="mt-[19px] flex items-center justify-between gap-2.5">
          <button
            className="cursor-pointer text-[11px] text-muted underline underline-offset-[3px]"
            onClick={close}
          >
            Salir de la guía
          </button>
          <div className="flex items-center gap-4">
            {index > 0 && (
              <IconButton aria-label="Paso anterior" onClick={() => setIndex(index - 1)}>
                <ArrowLeft size={17} />
              </IconButton>
            )}
            <Button size="walk" onClick={() => (last ? close() : setIndex(index + 1))}>
              {last ? (
                <>
                  <Check size={15} />
                  Finalizar
                </>
              ) : (
                <>
                  Siguiente
                  <ArrowRight size={15} />
                </>
              )}
            </Button>
          </div>
        </footer>
      </div>
    </>
  );
}
