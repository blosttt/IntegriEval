"use client";
import {useEffect,useMemo,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,X,Check} from 'lucide-react';
import {api} from '@/lib/api';
const baseSteps=[
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
type Box={top:number;left:number;width:number;height:number};
export default function TeacherTutorial({onStep,assistant=false}:{onStep:(tab:any)=>void;assistant?:boolean}){
 const [open,setOpen]=useState(false),[index,setIndex]=useState(0),[key,setKey]=useState(''),[box,setBox]=useState<Box|null>(null),[viewport,setViewport]=useState({width:1000,height:800});
 const tip=useRef<HTMLDivElement>(null),previousFocus=useRef<HTMLElement|null>(null),stepCallback=useRef(onStep);stepCallback.current=onStep;
 const steps=useMemo(()=>baseSteps.filter(step=>!assistant||!step.teacherOnly).map(step=>assistant&&step.target==='student-roster'?{...step,text:'Puedes consultar la nómina y los correos de este curso. Como ayudante no puedes agregar, importar, editar ni retirar alumnos. El resto del flujo de evaluación está habilitado.'}:step),[assistant]);
 useEffect(()=>{let alive=true;api.getMe().then(user=>{if(!alive||!['docente','ayudante'].includes(user.rol))return;const k=`integryeval:walkthrough:v2:${user.id}`;setKey(k);if(!localStorage.getItem(k)){previousFocus.current=document.activeElement as HTMLElement;setIndex(0);setOpen(true);}}).catch(()=>{});
  const start=()=>{previousFocus.current=document.activeElement as HTMLElement;setIndex(0);setOpen(true);};window.addEventListener('integryeval:open-tutorial',start);return()=>{alive=false;window.removeEventListener('integryeval:open-tutorial',start);};
 },[]);
 const close=()=>{if(key)localStorage.setItem(key,'seen');setOpen(false);setBox(null);previousFocus.current?.focus();};
 useEffect(()=>{if(!open)return;stepCallback.current(steps[index].tab);setBox(null);let frame=0,attempt=0,element:HTMLElement|null=null,resize:ResizeObserver|null=null;
  const measure=()=>{if(!element)return;const r=element.getBoundingClientRect(),w=window.innerWidth,h=window.innerHeight;
    const top=Math.max(8,r.top-7),left=Math.max(8,r.left-7),right=Math.min(w-8,r.right+7),bottom=Math.min(h-8,r.bottom+7);
    setViewport({width:w,height:h});const next={top,left,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
    setBox(old=>old&&Math.abs(old.top-next.top)<1&&Math.abs(old.left-next.left)<1&&Math.abs(old.width-next.width)<1&&Math.abs(old.height-next.height)<1?old:next);
  };
  const locate=()=>{element=document.querySelector<HTMLElement>(`[data-tour="${steps[index].target}"]`);if(!element&&attempt++<90){frame=requestAnimationFrame(locate);return;}
    if(!element)element=document.querySelector<HTMLElement>(`[data-tour="tab-${steps[index].tab}"]`);
    if(element){element.scrollIntoView({behavior:'smooth',block:'center',inline:'nearest'});resize=new ResizeObserver(measure);resize.observe(element);measure();}
  };
  frame=requestAnimationFrame(locate);window.addEventListener('scroll',measure,true);window.addEventListener('resize',measure);
  return()=>{cancelAnimationFrame(frame);resize?.disconnect();window.removeEventListener('scroll',measure,true);window.removeEventListener('resize',measure);};
 },[open,index,steps]);
 useEffect(()=>{if(!open)return;const escape=(event:KeyboardEvent)=>{if(event.key==='Escape')close();};document.addEventListener('keydown',escape);return()=>document.removeEventListener('keydown',escape);},[open,key]);
 useEffect(()=>{if(open&&box)tip.current?.focus({preventScroll:true});},[open,index,!!box]);
 if(!open)return null;
 const width=Math.min(366,viewport.width-32),height=tip.current?.offsetHeight||300;let left=(viewport.width-width)/2,top=viewport.height-height-20;
 if(box){if(box.left+box.width+width+28<viewport.width){left=box.left+box.width+16;top=box.top;}else if(box.left-width-24>0){left=box.left-width-16;top=box.top;}else{left=Math.max(16,Math.min(box.left,viewport.width-width-16));top=box.top+box.height+height+24<viewport.height?box.top+box.height+16:box.top-height-16;}}
 top=Math.max(16,Math.min(top,viewport.height-height-16));
 return <>{box&&box.width>0&&box.height>0&&<div className="ie-spotlight" data-testid="tour-highlight" aria-hidden="true" style={{top:box.top,left:box.left,width:box.width,height:box.height}}/>}
   <div ref={tip} role="dialog" aria-modal="false" aria-labelledby="walkthrough-title" tabIndex={-1} className="ie-walkthrough" style={{top,left,width}} data-testid="tour-tooltip">
     <div className="ie-walkthrough-top"><span>Guía de uso · {index+1} / {steps.length}</span><button className="ie-icon-button" onClick={close} aria-label="Cerrar guía"><X size={17}/></button></div>
     <div className="ie-tour-progress" aria-label={`Paso ${index+1} de ${steps.length}`}>{steps.map((s,i)=><span key={s.target} className={i<=index?'complete':''}/>)}</div>
     <h2 id="walkthrough-title">{steps[index].title.replace(/^\d+\. /,'')}</h2><p>{steps[index].text}</p><span className="ie-walkthrough-hint">Puedes interactuar con el elemento destacado. La guía no modifica datos por ti.</span>
     <footer><button className="ie-walkthrough-skip" onClick={close}>Salir de la guía</button><div className="ie-actions">{index>0&&<button className="ie-icon-button" aria-label="Paso anterior" onClick={()=>setIndex(index-1)}><ArrowLeft size={17}/></button>}<button className="ie-button ie-primary" onClick={()=>index===steps.length-1?close():setIndex(index+1)}>{index===steps.length-1?<><Check size={15}/>Finalizar</>:<>Siguiente<ArrowRight size={15}/></>}</button></div></footer>
   </div>
 </>;
}
