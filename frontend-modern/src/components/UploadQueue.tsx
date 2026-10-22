"use client";
import {useEffect,useRef,useState} from 'react';
import {request} from '@/lib/api';
export default function UploadQueue({courseId,evaluationId,onCompleted}:{courseId:number;evaluationId:number;onCompleted:()=>void}){
 const [jobs,setJobs]=useState<any[]>([]),[error,setError]=useState('');
 const callback=useRef(onCompleted);callback.current=onCompleted;
 const completed=useRef('');
 const activity=evaluationId<0?-evaluationId:0,root=`/asignaturas/${courseId}/cargas`;
 const labels:any={pending:'En cola',running:'Procesando',completed:'Completado',failed:'Error',cancelled:'Cancelado'};
 useEffect(()=>{let active=true,timer:ReturnType<typeof setTimeout>;completed.current='';const load=async()=>{try{const data=await request(root+(activity?'?actividad_id='+activity:''));if(!active)return;setJobs(data);const signature=data.filter((j:any)=>j.status==='completed').map((j:any)=>`${j.id}:${j.attempts}`).join(',');if(completed.current&&completed.current!==signature)callback.current();if(!completed.current&&signature)callback.current();completed.current=signature;}catch(e:any){if(active)setError(e.message);}if(active)timer=setTimeout(load,3000);};load();const refresh=()=>{clearTimeout(timer);load();};window.addEventListener('integryeval:uploads-queued',refresh);return()=>{active=false;clearTimeout(timer);window.removeEventListener('integryeval:uploads-queued',refresh);};},[courseId,evaluationId]);
 const finished=jobs.filter(j=>['completed','failed','cancelled'].includes(j.status)).length;
 return <section className="ie-panel"><h3>Procesamiento de archivos</h3><p>{jobs.length?`${finished} de ${jobs.length} archivos finalizados`:'No hay archivos en cola para esta evaluación.'}</p>{!!jobs.length&&<progress aria-label="Archivos finalizados" value={finished} max={jobs.length} style={{width:'100%'}}/>}<p className="ie-muted">Puedes cancelar los archivos pendientes. Los que ya empezaron terminan su procesamiento.</p>{error&&<p className="ie-error" role="alert">{error}</p>}{jobs.map(job=><article className="ie-course" key={job.id}><div><strong>{job.filename}</strong><p>{labels[job.status]||job.status} · intento {job.attempts}{job.error?' · '+job.error:''}</p></div>{['pending','failed','cancelled'].includes(job.status)&&<button className="ie-button" onClick={async()=>{try{const result=await request(`${root}/${job.id}/${job.status==='pending'?'cancelar':'reintentar'}`,'POST');setJobs(items=>items.map(j=>j.id===job.id?result:j));}catch(e:any){setError(e.message);}}}>{job.status==='pending'?'Cancelar':'Reintentar'}</button>}</article>)}</section>;
}
