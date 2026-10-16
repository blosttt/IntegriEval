import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IntegryEval - Validación de Autoría Académica",
  description: "Plataforma de validación de comprensión y autoría de informes académicos basada en inteligencia artificial.",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
