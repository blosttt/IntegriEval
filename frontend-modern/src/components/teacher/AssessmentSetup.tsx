"use client";

import { useEffect, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Banner, Button, Field, Hint, Input, Panel, Select, Textarea } from "./ui";

type Criterion = { nombre: string; descripcion: string; peso: number };
type Setup = { version?: number; criterios: Criterion[]; temas: string; rubrica_id: number | null; materiales_clase: number[]; materiales_semestre: number[] };
type Material = { id: number; tipo: string; nombre: string };
const blank: Setup = { criterios: [{ nombre: "", descripcion: "", peso: 100 }], temas: "", rubrica_id: null, materiales_clase: [], materiales_semestre: [] };

export default function AssessmentSetup({ evaluationId, readOnly }: { evaluationId: number; readOnly: boolean }) {
  const [data, setData] = useState<Setup>(blank);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [templates, setTemplates] = useState<{ nombre: string; criterios: Criterion[] }[]>([]);
  const [templateName, setTemplateName] = useState("");
  const [file, setFile] = useState<File>();
  const [kind, setKind] = useState("rubrica");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([api.getAssessmentSetup(evaluationId), api.getMaterials(evaluationId), api.getRubricTemplates(evaluationId)])
      .then(([setup, files, saved]) => { if (active) { setData(setup || blank); setMaterials(files); setTemplates(saved); } })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [evaluationId]);

  const change = (index: number, update: Partial<Criterion>) => setData(previous => ({
    ...previous, criterios: previous.criterios.map((row, i) => i === index ? { ...row, ...update } : row),
  }));
  const update = async (action: () => Promise<void>) => {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  };
  const save = (event: FormEvent) => {
    event.preventDefault();
    void update(async () => {
      const { version, ...payload } = data;
      setData(await api.saveAssessmentSetup(evaluationId, payload));
      setMessage("Rúbrica guardada. Se aplicará al próximo análisis del informe.");
    });
  };
  const assign = (id: number, target: string) => setData(previous => ({
    ...previous,
    materiales_clase: [...previous.materiales_clase.filter(value => value !== id), ...(target === "clase" ? [id] : [])],
    materiales_semestre: [...previous.materiales_semestre.filter(value => value !== id), ...(target === "semestre" ? [id] : [])],
  }));
  const upload = () => {
    if (!file) return;
    void update(async () => {
      const material = await api.uploadMaterial(evaluationId, file.name, file, kind === "rubrica" ? "rubrica" : "guia");
      setMaterials(previous => [...previous, material]);
      if (kind === "rubrica") setData(previous => ({ ...previous, rubrica_id: material.id }));
      else assign(material.id, kind);
      setFile(undefined);
      setMessage("Archivo cargado. Guarda la preparación para aplicarlo.");
    });
  };

  return <Panel className="lg:col-span-3">
    <h2 className="text-lg font-bold">Rúbrica, temas y materiales de la evaluación</h2>
    <Hint>Confirma los criterios y sus pesos. El informe y el Flash Test se podrán revisar con la misma rúbrica.</Hint>
    {error && <Banner tone="error" role="alert">{error}</Banner>}
    {message && <p role="status" className="text-sm">{message}</p>}
    <form onSubmit={save} className="space-y-4">
      <fieldset disabled={busy || readOnly} className="space-y-4">
        <div className="flex flex-wrap items-end gap-2">
          <Field label="Plantilla de rúbrica"><Select value="" onChange={e => {
            const template = templates.find(item => item.nombre === e.target.value);
            if (template) setData(previous => ({ ...previous, criterios: template.criterios, rubrica_id: null }));
          }}>
            <option value="">Cargar plantilla guardada</option>
            {templates.map(item => <option key={item.nombre}>{item.nombre}</option>)}
          </Select></Field>
          <Field label="Nombre de la plantilla"><Input maxLength={120} value={templateName} onChange={e => setTemplateName(e.target.value)} /></Field>
          <Button type="button" variant="outline" disabled={!templateName.trim()} onClick={() => void update(async () => {
            const item = await api.saveRubricTemplate(evaluationId, { nombre: templateName, criterios: data.criterios });
            setTemplates(previous => [...previous, item]);
            setTemplateName("");
            setMessage("Plantilla guardada para otras evaluaciones del curso.");
          })}>Guardar como plantilla</Button>
        </div>
        <Field label="Temas que se evaluarán"><Textarea required maxLength={4000} value={data.temas} onChange={e => setData({ ...data, temas: e.target.value })} /></Field>
        {data.criterios.map((row, index) => <div key={index} className="grid gap-2 rounded-control border border-line p-3 md:grid-cols-[1fr_2fr_110px_auto]">
          <Field label="Criterio"><Input required maxLength={100} value={row.nombre} onChange={e => change(index, { nombre: e.target.value })} /></Field>
          <Field label="Qué se evalúa"><Textarea required maxLength={1000} rows={2} value={row.descripcion} onChange={e => change(index, { descripcion: e.target.value })} /></Field>
          <Field label="Peso (%)"><Input required type="number" min={1} max={100} value={row.peso || ""} onChange={e => change(index, { peso: Number(e.target.value) })} /></Field>
          <Button type="button" variant="outline" disabled={data.criterios.length === 1} onClick={() => setData({ ...data, criterios: data.criterios.filter((_, i) => i !== index) })}>Quitar</Button>
        </div>)}
        <Button type="button" variant="outline" disabled={data.criterios.length >= 10} onClick={() => setData({ ...data, criterios: [...data.criterios, { nombre: "", descripcion: "", peso: 0 }] })}>Agregar criterio</Button>
        <Field label="Documento de rúbrica (opcional)">
          <Select value={data.rubrica_id ?? ""} onChange={e => setData({ ...data, rubrica_id: Number(e.target.value) || null })}>
            <option value="">Usar los criterios ingresados</option>
            {materials.filter(m => m.tipo === "rubrica").map(m => <option value={m.id} key={m.id}>{m.nombre}</option>)}
          </Select>
        </Field>
        {materials.filter(m => m.tipo !== "rubrica").map(m => <Field key={m.id} label={m.nombre}>
          <Select value={data.materiales_clase.includes(m.id) ? "clase" : data.materiales_semestre.includes(m.id) ? "semestre" : ""} onChange={e => assign(m.id, e.target.value)}>
            <option value="">Fuera de esta evaluación</option>
            <option value="clase">Material de clase</option>
            <option value="semestre">Material del semestre</option>
          </Select>
        </Field>)}
        <div className="flex flex-wrap items-end gap-2">
          <Field label="Categoría del archivo"><Select value={kind} onChange={e => setKind(e.target.value)}>
            <option value="rubrica">Rúbrica</option><option value="clase">Material de clase</option><option value="semestre">Material del semestre</option>
          </Select></Field>
          <Field label="PDF, Markdown o texto"><Input type="file" accept=".pdf,.md,.markdown,.txt" onChange={e => setFile(e.target.files?.[0])} /></Field>
          <Button type="button" variant="outline" disabled={!file} onClick={upload}>Cargar material</Button>
        </div>
        <Button type="submit">Guardar preparación</Button>
        {data.version && <Hint>Rúbrica guardada · versión {data.version}</Hint>}
      </fieldset>
    </form>
  </Panel>;
}
