"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { request } from "@/lib/api";
import {
  Banner,
  Button,
  FormField,
  FormInput,
  buttonClasses,
  formStackClasses,
  shellClasses,
  studentHeadingClasses,
  studentMainClasses,
  studentPanelClasses,
} from "@/components/ui";

export default function Recover() {
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    setToken(new URLSearchParams(location.search).get("token") || "");
  }, []);

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(e.currentTarget);
    if (token && data.get("password") !== data.get("confirm")) {
      setError("Las contraseñas no coinciden.");
      setBusy(false);
      return;
    }
    try {
      const result = await request(
        "/auth/" + (token ? "reset-password" : "forgot-password"),
        "POST",
        token ? { token, contrasena: String(data.get("password")) } : { correo: String(data.get("email")) },
      );
      setMessage(result.message);
      setDone(true);
      if (token) {
        history.replaceState(null, "", "/recuperar");
        setToken("");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={shellClasses}>
      <Navbar />
      <main className={studentMainClasses}>
        <section className={studentPanelClasses}>
          <h1 className={studentHeadingClasses}>{token ? "Nueva contraseña" : "Recuperar acceso"}</h1>
          <p>
            {token
              ? "El enlace se puede usar una sola vez y caduca en 30 minutos."
              : "Ingresa el correo de tu cuenta docente o administrativa."}
          </p>
          {!done && (
            <form className={`${formStackClasses} text-left`} onSubmit={submit}>
              {token ? (
                <>
                  <FormField label="Nueva contraseña">
                    <FormInput
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      minLength={10}
                      required
                    />
                  </FormField>
                  <FormField label="Confirmar contraseña">
                    <FormInput
                      name="confirm"
                      type="password"
                      autoComplete="new-password"
                      minLength={10}
                      required
                    />
                  </FormField>
                </>
              ) : (
                <FormField label="Correo institucional">
                  <FormInput name="email" type="email" autoComplete="email" required />
                </FormField>
              )}
              <Button type="submit" size="classic" disabled={busy}>
                {busy ? "Procesando…" : token ? "Guardar nueva contraseña" : "Solicitar enlace"}
              </Button>
            </form>
          )}
          {message && <p role="status">{message}</p>}
          {error && (
            <Banner tone="error" role="alert">
              {error}
            </Banner>
          )}
          <Link className={buttonClasses("surface", "classic")} href="/#acceso">
            Volver al inicio de sesión
          </Link>
        </section>
      </main>
    </div>
  );
}
