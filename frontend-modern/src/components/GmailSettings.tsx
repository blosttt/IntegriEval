"use client";

import { useState, type FormEvent } from "react";
import Dialog from "./Dialog";
import { request } from "@/lib/api";
import {
  Banner,
  Button,
  FormField,
  FormInput,
  FormSelect,
  FormStack,
  MutedText,
  formStackClasses,
} from "./ui";

const sectionTitle = "text-[15px] font-semibold";

export default function GmailSettings() {
  const [data, setData] = useState<any>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [port, setPort] = useState(587);
  const [url, setUrl] = useState("");
  const [recipient, setRecipient] = useState("");
  const [received, setReceived] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const dirty =
    !!data &&
    (email.toLowerCase() !== data.correo.toLowerCase() ||
      !!password ||
      port !== data.port ||
      url.replace(/\/$/, "") !== data.public_url);

  const open = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await request("/admin/correo");
      setData(result);
      setEmail(result.correo || "");
      setPort(result.port === 465 ? 465 : 587);
      setUrl(result.public_url || "");
      setRecipient(result.correo || "");
      setPassword("");
      setReceived(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const close = () => {
    if (busy) return;
    setData(null);
    setPassword("");
    setError("");
    setMessage("");
  };

  const toggle = async (enabled: boolean) => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      setData(await request("/admin/correo/estado", "POST", { enabled, received }));
      setMessage(
        enabled
          ? "Envíos activados. Los nuevos avisos usarán esta cuenta."
          : "Envíos desactivados.",
      );
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const saveConfig = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await request("/admin/correo", "PUT", {
        correo: email,
        ...(password ? { password } : {}),
        port,
        public_url: url,
      });
      setData(result);
      setEmail(result.correo);
      setUrl(result.public_url);
      setPassword("");
      setReceived(false);
      if (!recipient) setRecipient(result.correo);
      setMessage(
        result.enabled
          ? "Configuración guardada."
          : "Configuración guardada. Envía una prueba antes de activar los envíos.",
      );
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const sendTest = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await request("/admin/correo/prueba", "POST", { recipient });
      setData(result);
      setReceived(false);
      setMessage(result.message);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button variant="surface" size="classic" disabled={busy} onClick={open}>
        Configurar correo Gmail
      </Button>
      {error && !data && (
        <Banner tone="error" role="alert">
          {error}
        </Banner>
      )}
      {data && (
        <Dialog title="Correo · Gmail / Google Workspace" wide onClose={close}>
          <FormStack>
            <p>
              <strong>Estado:</strong> {data.enabled ? "Envíos activados" : "Envíos desactivados"}.{" "}
              {data.password_configured
                ? "Hay una contraseña guardada; no se muestra ni se devuelve al navegador."
                : "Falta guardar la cuenta y su contraseña de aplicación."}
            </p>
            <p>
              Usa una{" "}
              <a
                href="https://support.google.com/accounts/answer/185833?hl=es"
                target="_blank"
                rel="noreferrer"
                className="text-brand-ink underline"
              >
                contraseña de aplicación de Google
              </a>
              , con verificación en dos pasos. No uses la contraseña normal de tu cuenta. En Google
              Workspace, su disponibilidad depende de las políticas de la institución.
            </p>
            {error && (
              <Banner tone="error" role="alert">
                {error}
              </Banner>
            )}
            {message && <p role="status">{message}</p>}
            <form className={formStackClasses} onSubmit={saveConfig}>
              <h3 className={sectionTitle}>1. Guardar configuración</h3>
              <FormField label="Cuenta de Gmail o Google Workspace">
                <FormInput
                  name="smtp-email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </FormField>
              <FormField
                label={`Contraseña de aplicación ${data.password_configured ? "(deja vacío para conservarla)" : ""}`}
              >
                <FormInput
                  name="smtp-password"
                  type="password"
                  autoComplete="new-password"
                  required={
                    !data.password_configured || email.toLowerCase() !== data.correo.toLowerCase()
                  }
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </FormField>
              <FormField label="Conexión segura">
                <FormSelect value={port} onChange={(e) => setPort(Number(e.target.value))}>
                  <option value={587}>smtp.gmail.com · 587 · STARTTLS</option>
                  <option value={465}>smtp.gmail.com · 465 · TLS</option>
                </FormSelect>
              </FormField>
              <FormField label="URL de IntegryEval para los enlaces">
                <FormInput
                  name="public-url"
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
              </FormField>
              <MutedText>
                Una dirección localhost solo se puede abrir en este equipo. Para los alumnos usa una
                URL que ellos puedan alcanzar.
              </MutedText>
              <Button type="submit" size="classic" disabled={busy}>
                Guardar configuración
              </Button>
            </form>
            <form className={formStackClasses} onSubmit={sendTest}>
              <h3 className={sectionTitle}>2. Enviar una prueba</h3>
              <FormField label="Correo que recibirá la prueba">
                <FormInput
                  name="test-recipient"
                  type="email"
                  required
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                />
              </FormField>
              <MutedText>Solo se enviará a esta dirección. No incluye datos de alumnos.</MutedText>
              <Button
                type="submit"
                variant="surface"
                size="classic"
                disabled={busy || !data.password_configured || dirty}
              >
                Enviar correo de prueba
              </Button>
              {dirty && <p>Guarda los cambios antes de enviar la prueba.</p>}
            </form>
            <section className={formStackClasses}>
              <h3 className={sectionTitle}>3. Activar envíos</h3>
              {data.verified && (
                <p>
                  La configuración actual tiene una prueba aceptada por Gmail para{" "}
                  {data.test_recipient}.
                </p>
              )}
              {data.enabled ? (
                <Button variant="surface" size="classic" disabled={busy} onClick={() => toggle(false)}>
                  Desactivar envíos
                </Button>
              ) : (
                <>
                  <label className="flex items-center gap-2 text-xs text-muted">
                    <input
                      type="checkbox"
                      checked={received}
                      disabled={busy || !data.verified || dirty}
                      onChange={(e) => setReceived(e.target.checked)}
                    />
                    Confirmo que recibí el correo de prueba.
                  </label>
                  <Button
                    size="classic"
                    disabled={busy || !data.verified || dirty || !received}
                    onClick={() => toggle(true)}
                  >
                    Activar envíos
                  </Button>
                </>
              )}
            </section>
          </FormStack>
        </Dialog>
      )}
    </>
  );
}
