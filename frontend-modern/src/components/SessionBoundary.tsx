"use client";

import { Fragment, useEffect, useRef, useState, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api";

export default function SessionBoundary({ children }: { children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [revision, setRevision] = useState(0);
  const [verified, setVerified] = useState(false);
  const [verifiedPath, setVerifiedPath] = useState("");
  const [error, setError] = useState("");
  const lastToken = useRef<string | null>(null);
  const retry = useRef<() => void>(() => {});
  const protectedPage = /^\/(teacher|assistant|admin)(\/|$)/.test(path);

  useEffect(() => {
    let active = true, sequence = 0;
    const sync = async () => {
      const token = getToken();
      const current = ++sequence;
      if (lastToken.current !== token) {
        lastToken.current = token;
        setVerified(false);
        setRevision(value => value + 1);
      }
      if (!token) {
        setVerified(false);
        if (protectedPage) router.replace('/#acceso');
        return;
      }
      try {
        const user = await api.getMe();
        if (!active || current !== sequence || getToken() !== token) return;
        const destination = user.rol === 'admin' ? '/admin/dashboard'
          : user.rol === 'ayudante' ? '/assistant/dashboard' : '/teacher/dashboard';
        const denied = (path.startsWith('/admin') && user.rol !== 'admin')
          || (path.startsWith('/teacher') && !['admin', 'docente'].includes(user.rol))
          || (path.startsWith('/assistant') && user.rol !== 'ayudante');
        if (denied) { setVerified(false); router.replace(destination); }
        else { setVerified(true); setVerifiedPath(path); }
        setError("");
      } catch {
        if (active && current === sequence && getToken() === token)
          setError("No pudimos verificar la sesión. La conexión se reintentará; tu sesión se conserva.");
      }
    };
    retry.current = () => { void sync(); };
    const event = () => { void sync(); };
    const storage = (e: StorageEvent) => { if (e.key === 'integrieval_token' || e.key === null) event(); };
    const visibility = () => { if (document.visibilityState === 'visible') event(); };
    event();
    const timer = setInterval(event, 60000);
    window.addEventListener('storage', storage);
    window.addEventListener('integryeval:session-changed', event);
    window.addEventListener('focus', event);
    window.addEventListener('pageshow', event);
    document.addEventListener('visibilitychange', visibility);
    return () => {
      active = false; sequence++;
      clearInterval(timer);
      window.removeEventListener('storage', storage);
      window.removeEventListener('integryeval:session-changed', event);
      window.removeEventListener('focus', event);
      window.removeEventListener('pageshow', event);
      document.removeEventListener('visibilitychange', visibility);
    };
  }, [path, protectedPage, router]);

  if (protectedPage && (!verified || verifiedPath !== path)) return <main className="min-h-screen bg-canvas p-10 text-fg" role="status">
    <p>{error || "Verificando sesión…"}</p>
    {error && <button className="mt-4 rounded border border-line px-4 py-2" onClick={() => retry.current()}>Reintentar conexión</button>}
  </main>;
  return <Fragment key={revision}>{children}</Fragment>;
}
