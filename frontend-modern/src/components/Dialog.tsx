"use client";
import {useEffect, useRef} from 'react';
import {X} from 'lucide-react';

export default function Dialog({title, children, onClose, wide=false}:{title:string;children:React.ReactNode;onClose:()=>void;wide?:boolean}) {
  const ref=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement;
    const previousOverflow=document.body.style.overflow;
    document.body.style.overflow='hidden';
    ref.current?.querySelector<HTMLElement>('button,input,select,textarea')?.focus();
    const handler=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.preventDefault();onClose();}
      if(event.key==='Tab'){
        const items=Array.from(ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]')||[]);
        const first=items[0],last=items[items.length-1];
        if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
      }
    };
    document.addEventListener('keydown',handler);
    return()=>{document.body.style.overflow=previousOverflow;document.removeEventListener('keydown',handler);previous?.focus();};
  },[]);
  return <div className="ie-overlay" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}>
    <div className={`ie-dialog ${wide?'ie-dialog-wide':''}`} role="dialog" aria-modal="true" aria-labelledby="ie-dialog-title" ref={ref}>
      <header><h2 id="ie-dialog-title">{title}</h2><button className="ie-icon-button" onClick={onClose} aria-label="Cerrar modal"><X size={19}/></button></header>
      {children}
    </div>
  </div>;
}
