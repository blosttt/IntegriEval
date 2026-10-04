import fitz  # PyMuPDF
from pathlib import Path

def generate_sample_pdf():
    output_dir = Path(__file__).resolve().parent
    output_path = output_dir / "carlos_alumno_informe_final.pdf"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size

    # Title
    page.insert_text(fitz.Point(50, 60), "INFORME DE PROYECTO: ARQUITECTURA DE SOFTWARE DISTRIBUIDA", fontsize=14, fontname="helv", color=(0, 0, 0))
    page.insert_text(fitz.Point(50, 80), "Estudiante: Carlos Alumno Pérez (carlos.alumno@alumnos.universidad.cl)", fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
    page.insert_text(fitz.Point(50, 95), "Asignatura: INFO1197 - Septiembre 2026", fontsize=10, fontname="helv", color=(0.4, 0.4, 0.4))

    # Section 1
    page.insert_text(fitz.Point(50, 130), "1. Introducción y Planteamiento del Problema", fontsize=12, fontname="helv", color=(0, 0.2, 0.6))
    intro_text = (
        "En conclusión, es fundamental destacar que la democratización de las arquitecturas basadas en eventos "
        "ha transformado la ingeniería moderna. El presente informe aborda el diseño de una plataforma tolerante "
        "a fallos para el procesamiento masivo de datos en tiempo real. Se evaluaron las alternativas de paso de "
        "mensajes frente a invocaciones sincrónicas REST, determinando que los brokers basados en colas distribuidas "
        "garantizan consistencia eventual y escalabilidad horizontal ante picos de concurrencia."
    )
    rect1 = fitz.Rect(50, 140, 545, 230)
    page.insert_textbox(rect1, intro_text, fontsize=10, fontname="helv")

    # Section 2
    page.insert_text(fitz.Point(50, 245), "2. Metodología y Decisiones de Arquitectura", fontsize=12, fontname="helv", color=(0, 0.2, 0.6))
    metodologia_text = (
        "Se adoptó un enfoque modular orientado a microservicios desacoplados. La capa de persistencia "
        "utiliza almacenamiento relacional para los registros transaccionales y auditoría inmutable, complementado "
        "con sockets asíncronos para la comunicación bidireccional en tiempo real con latencias inferiores a 50 milisegundos. "
        "Para validar el rendimiento, se ejecutaron pruebas de estrés simulando 100 conexiones concurrentes, "
        "obteniendo tiempos de respuesta en el percentil 95 menores a 200 ms."
    )
    rect2 = fitz.Rect(50, 255, 545, 360)
    page.insert_textbox(rect2, metodologia_text, fontsize=10, fontname="helv")

    # Section 3
    page.insert_text(fitz.Point(50, 375), "3. Resultados, Discusión y Conclusiones", fontsize=12, fontname="helv", color=(0, 0.2, 0.6))
    resultados_text = (
        "Los resultados empíricos demuestran que la combinación de un motor heurístico local con verificación "
        "flash personalizada reduce la incertidumbre en los procesos evaluativos masivos. En última instancia, "
        "el juicio del docente permanece como el componente decisorio indispensable para garantizar justicia y "
        "validez pedagógica. Como trabajo futuro, se contempla ampliar la integración con sistemas institucionales "
        "y profundizar en la calibración de perplejidad léxica."
    )
    rect3 = fitz.Rect(50, 385, 545, 490)
    page.insert_textbox(rect3, resultados_text, fontsize=10, fontname="helv")

    doc.save(str(output_path))
    doc.close()
    print(f"Sample PDF created successfully at: {output_path}")

if __name__ == "__main__":
    generate_sample_pdf()
