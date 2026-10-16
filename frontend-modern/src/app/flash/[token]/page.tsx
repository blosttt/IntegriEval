"use client";
import {useEffect} from 'react';
export default function Flash(){useEffect(()=>{window.location.replace('/test/'+encodeURIComponent(window.location.pathname.split('/').pop() || ''));},[]);return <p>Abriendo sesión de verificación segura…</p>;}
