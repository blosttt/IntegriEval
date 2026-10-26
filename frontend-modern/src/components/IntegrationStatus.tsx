"use client";

import { useState } from "react";
import { request } from "@/lib/api";
import Dialog from "./Dialog";
import { Button, FormStack } from "./ui";

export default function IntegrationStatus() {
  const [message, setMessage] = useState("");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setData(await request("/admin/integraciones"));
    } catch (e: any) {
      setError(e.message);
    }
  };

  const testAi = async () => {
    try {
      setMessage((await request("/admin/integraciones/probar-ia", "POST")).message);
    } catch (e: any) {
      setMessage(e.message);
    }
  };

  return (
    <>
      <Button variant="surface" size="classic" onClick={load}>
        Estado de integraciones
      </Button>
      {error && <p role="alert">{error}</p>}
      {data && (
        <Dialog title="Estado de integraciones" onClose={() => setData(null)}>
          <FormStack>
            {message && <p role="status">{message}</p>}
            <Button variant="surface" size="classic" onClick={testAi}>
              Probar conexión de IA
            </Button>
            <p>
              <strong>IA:</strong> {data.llm.provider} · {data.llm.model} ·{" "}
              {data.llm.simulated
                ? "Modo simulado"
                : data.llm.configured
                  ? "Configurada; requiere prueba real"
                  : "Falta configurar credenciales"}
            </p>
            <p>
              <strong>Correo:</strong>{" "}
              {data.smtp.enabled && data.smtp.configured
                ? "Habilitado; requiere prueba de entrega"
                : "Desactivado o incompleto"}
            </p>
            <p>
              <strong>Enlaces públicos:</strong> {data.smtp.public_url}
            </p>
            <p>
              <strong>OCR:</strong>{" "}
              {data.ocr.enabled && data.ocr.trained_data_ready
                ? "Habilitado"
                : "Desactivado o faltan datos de idioma"}{" "}
              · {data.ocr.language}
            </p>
            <p>
              La configuración se lee de .env en el servidor. Este panel no muestra claves ni
              contraseñas.
            </p>
          </FormStack>
        </Dialog>
      )}
    </>
  );
}
