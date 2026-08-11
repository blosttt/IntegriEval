"use client";

import React, { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ShieldAlert, Clock, AlertOctagon, HelpCircle, 
  CheckCircle, XCircle, ArrowRight, BookOpen, LogOut 
} from "lucide-react";
import { api, getToken, getRole, getWsBase } from "@/lib/api";

interface Question {
  question_id: number;
  text: string;
  q_type: string;
  options: string[] | null;
  index: number;
  total: number;
  limit_seconds: number;
}

export default function EvalSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = Number(params.id);

  const [session, setSession] = useState<any>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [answered, setAnswered] = useState(false);
  const [resultCorrect, setResultCorrect] = useState<boolean | null>(null);
  const [finished, setFinished] = useState(false);
  const [finalScore, setFinalScore] = useState<any>(null);
  const [socketError, setSocketError] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [focusLosses, setFocusLosses] = useState(0);
  const [warningMessage, setWarningMessage] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<any>(null);

  // 1. Authenticate and verify session ownership on load
  useEffect(() => {
    const token = getToken();
    const role = getRole();
    if (!token || role !== "student") {
      router.push("/login");
      return;
    }

    // Load session status
    api.getSessionStatus(sessionId)
      .then((data) => {
        setSession(data);
        if (data.status === "completed") {
          setFinished(true);
          setFinalScore({
            score: data.score,
            percentage_score: data.percentage_score,
            classification: data.classification
          });
        } else {
          // Attempt entering fullscreen & connect WS
          requestFullscreen();
          connectWebSocket(token);
        }
      })
      .catch((err) => {
        setSocketError("No se pudo iniciar la conexión con el servidor");
      });

    // Clean up timers and websocket on unmount
    return () => {
      cleanup();
    };
  }, [sessionId, router]);

  // 2. Fullscreen & Proctoring Event Listeners
  useEffect(() => {
    if (finished) {
      exitFullscreen();
      return;
    }

    // A. Detect Fullscreen exits
    const handleFullscreenChange = () => {
      const isFull = !!document.fullscreenElement;
      setIsFullscreen(isFull);
      if (!isFull) {
        setWarningMessage("Debes estar en pantalla completa. Regresa para continuar la prueba.");
        logProctoringEvent("exit_fullscreen", { timestamp: new Date().toISOString() });
      } else {
        setWarningMessage("");
      }
    };

    // B. Detect Tab changes or Focus Loss (Visibility API)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setFocusLosses((prev) => {
          const next = prev + 1;
          logProctoringEvent("focus_lost", { count: next, trigger: "tab_hidden" });
          return next;
        });
        alert("ALERTA: Se ha detectado un cambio de pestaña. Esta acción ha sido registrada en la bitácora de auditoría.");
      }
    };

    const handleWindowBlur = () => {
      setFocusLosses((prev) => {
        const next = prev + 1;
        logProctoringEvent("focus_lost", { count: next, trigger: "window_blur" });
        return next;
      });
    };

    // C. Block copy-paste, right-click, select
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    const handleCopy = (e: ClipboardEvent) => {
      e.preventDefault();
      logProctoringEvent("copy_attempted");
    };
    const handlePaste = (e: ClipboardEvent) => e.preventDefault();
    const handleCut = (e: ClipboardEvent) => e.preventDefault();
    const handleKeyDown = (e: KeyboardEvent) => {
      // Disable keys: F12, Ctrl+Shift+I, Alt+Arrow
      if (
        e.key === "F12" || 
        (e.ctrlKey && e.shiftKey && e.key === "I") || 
        (e.altKey && e.key === "Tab")
      ) {
        e.preventDefault();
        logProctoringEvent("dev_tools_attempted", { key: e.key });
      }
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleWindowBlur);
    document.addEventListener("contextmenu", handleContextMenu);
    document.addEventListener("copy", handleCopy);
    document.addEventListener("paste", handlePaste);
    document.addEventListener("cut", handleCut);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleWindowBlur);
      document.removeEventListener("contextmenu", handleContextMenu);
      document.removeEventListener("copy", handleCopy);
      document.removeEventListener("paste", handlePaste);
      document.removeEventListener("cut", handleCut);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [finished]);

  // Log events to backend audit log
  const logProctoringEvent = async (action: string, extra = {}) => {
    try {
      const token = getToken();
      await fetch(`http://127.0.0.1:8000/api/session/${sessionId}/status`, {
        method: "GET", // Simple fetch fallback to keep ws clean
        headers: { "Authorization": `Bearer ${token}` }
      });
      // We also send a simple socket message if open
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          action: "log_proctoring",
          event: action,
          details: extra
        }));
      }
    } catch (e) {}
  };

  // Fullscreen controls
  const requestFullscreen = () => {
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
  };

  const exitFullscreen = () => {
    if (document.exitFullscreen && document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
  };

  // 3. Setup WebSocket Connection
  const connectWebSocket = (token: string) => {
    const wsUrl = `${getWsBase()}/session/ws/${sessionId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "question") {
        setQuestion({
          question_id: msg.question_id,
          text: msg.text,
          q_type: msg.q_type,
          options: msg.options,
          index: msg.index,
          total: msg.total,
          limit_seconds: msg.limit_seconds
        });
        setTimeLeft(msg.limit_seconds);
        setSelectedAnswer(null);
        setAnswered(false);
        setResultCorrect(null);
        startTimer(msg.limit_seconds);
      }

      else if (msg.type === "result") {
        setResultCorrect(msg.is_correct);
      }

      else if (msg.type === "timeout") {
        setAnswered(true);
        setResultCorrect(false);
      }

      else if (msg.type === "finished") {
        setFinished(true);
        setFinalScore({
          score: msg.score,
          percentage_score: msg.percentage_score,
          classification: msg.classification
        });
        cleanup();
      }
    };

    ws.onerror = (e) => {
      setSocketError("Error en la conexión en tiempo real");
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };
  };

  // 4. Timer Handling
  const startTimer = (seconds: number) => {
    if (timerRef.current) clearInterval(timerRef.current);
    
    let current = seconds;
    timerRef.current = setInterval(() => {
      current -= 1;
      if (current >= 0) {
        setTimeLeft(current);
      } else {
        clearInterval(timerRef.current);
      }
    }, 1000);
  };

  // 5. Submit Answer
  const handleSelectOption = (optionIndex: number) => {
    if (answered || !wsRef.current || !question) return;

    setSelectedAnswer(optionIndex.toString());
    setAnswered(true);

    // Calculate response time in ms
    const timeTakenMs = (question.limit_seconds - timeLeft) * 1000;

    // Send answer via WebSocket
    wsRef.current.send(JSON.stringify({
      action: "answer",
      question_id: question.question_id,
      answer: optionIndex.toString(),
      response_time_ms: timeTakenMs
    }));
  };

  const cleanup = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const getScoreClassificationLabel = (classification: string) => {
    if (classification === "low") return "Defensa Oral Programada";
    if (classification === "high") return "Resultado de Excelencia";
    return "Resultado Regular";
  };

  const getScoreClassificationStyle = (classification: string) => {
    if (classification === "low") return "text-red-400 bg-red-500/10 border-red-500/20";
    if (classification === "high") return "text-purple-400 bg-purple-500/10 border-purple-500/20";
    return "text-zinc-400 bg-zinc-900 border-zinc-800";
  };

  if (socketError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07070a] px-6 text-center">
        <div className="glass-panel p-8 rounded-2xl max-w-md space-y-4">
          <ShieldAlert className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">Error de Conexión</h2>
          <p className="text-sm text-zinc-400">{socketError}</p>
          <button 
            onClick={() => router.push("/student/dashboard")}
            className="rounded-xl bg-zinc-800 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-700"
          >
            Regresar al panel
          </button>
        </div>
      </div>
    );
  }

  // Warning for Fullscreen Exit
  if (warningMessage && !finished) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-red-950/20 backdrop-blur-md px-6 text-center">
        <div className="glass-panel border-red-500/30 p-8 rounded-2xl max-w-md space-y-6 animate-float">
          <AlertOctagon className="h-16 w-16 text-red-500 mx-auto" />
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Pantalla Completa Requerida</h2>
            <p className="text-sm text-red-300">
              Has salido del modo pantalla completa o has cambiado el foco. Esto infringe la política anti-copia del examen.
            </p>
          </div>
          <button 
            onClick={requestFullscreen}
            className="w-full rounded-xl bg-red-600 py-3 text-sm font-bold text-white shadow-lg hover:bg-red-500 transition-all cursor-pointer"
          >
            Reingresar a Pantalla Completa
          </button>
        </div>
      </div>
    );
  }

  // 6. Final Results Screen
  if (finished) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#07070a] px-6 py-12">
        <div className="glow-bg top-[10%] left-[20%]" />
        
        <div className="w-full max-w-md glass-panel p-8 rounded-2xl text-center space-y-6">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <BookOpen className="h-8 w-8" />
          </div>

          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold tracking-tight text-white">Evaluación Completada</h2>
            <p className="text-sm text-zinc-400">Respuestas registradas exitosamente en el servidor.</p>
          </div>

          {finalScore && (
            <div className="space-y-4 py-4">
              <div className="inline-block p-6 rounded-2xl bg-zinc-950/40 border border-zinc-900">
                <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider block">Calificación</span>
                <span className="text-4xl font-extrabold text-white mt-1 block">
                  {finalScore.score} / {question?.total || session?.evaluation?.num_questions || 5}
                </span>
                <span className="text-xs text-indigo-400 font-bold block mt-1">
                  {Math.round(finalScore.percentage_score * 100)}% de Logro
                </span>
              </div>

              <div>
                <span className={`inline-block text-xs font-bold px-3 py-1 rounded-full border uppercase tracking-wider ${getScoreClassificationStyle(finalScore.classification)}`}>
                  {getScoreClassificationLabel(finalScore.classification)}
                </span>
              </div>

              {finalScore.classification === "low" && (
                <p className="text-xs text-red-300 max-w-xs mx-auto leading-relaxed">
                  * Tu puntaje está bajo el umbral de aprobación. El sistema ha programado una defensa oral con tu profesor. Revisa los detalles en tu calendario.
                </p>
              )}
              {finalScore.classification === "high" && (
                <p className="text-xs text-purple-300 max-w-xs mx-auto leading-relaxed">
                  * ¡Felicitaciones! Rendimiento excepcional. Se ha programado una cita de verificación corta y el sistema ha seleccionado a un compañero aleatorio para validación.
                </p>
              )}
            </div>
          )}

          <button
            onClick={() => router.push("/student/dashboard")}
            className="flex items-center justify-center gap-2 w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-500 transition-all cursor-pointer"
          >
            <span>Ir al panel principal</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  // 7. Live Question Screen
  return (
    <div className="flex min-h-screen flex-col bg-[#07070a] select-none">
      
      {/* Header bar during test */}
      <header className="glass-panel px-6 py-4 flex items-center justify-between border-b">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-indigo-400" />
          <span className="text-sm font-bold text-zinc-300 uppercase tracking-wider">MODO EVALUACIÓN FLASH</span>
        </div>

        {question && (
          <span className="text-xs font-semibold text-zinc-400 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full">
            Pregunta {question.index + 1} de {question.total}
          </span>
        )}
      </header>

      {/* Main workspace */}
      <main className="flex-1 flex flex-col items-center justify-center max-w-2xl w-full mx-auto px-6 py-12 gap-8">
        
        {/* Timer UI */}
        {question && (
          <div className="flex flex-col items-center gap-2">
            <div className={`relative h-20 w-20 rounded-full flex items-center justify-center border-4 ${
              timeLeft <= 5 ? "border-red-500 animate-pulse text-red-400" : "border-indigo-600 text-indigo-400"
            } bg-zinc-950/80 transition-colors`}>
              <Clock className="absolute h-10 w-10 opacity-10" />
              <span className="text-2xl font-black">{timeLeft}</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Segundos restantes</span>
          </div>
        )}

        {/* Question Panel */}
        {question ? (
          <div className="w-full space-y-8 text-center">
            {/* Question Text */}
            <div className="glass-panel p-6 rounded-2xl border-l-4 border-l-indigo-500 text-left">
              <span className="inline-block text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded uppercase tracking-wider mb-3">
                {question.q_type === "multiple_choice" ? "Selección Múltiple" : "Verdadero / Falso"}
              </span>
              <h2 className="text-xl sm:text-2xl font-bold text-zinc-100 leading-snug">
                {question.text}
              </h2>
            </div>

            {/* Answer Options */}
            <div className="grid grid-cols-1 gap-4 text-left">
              {question.options?.map((opt, i) => {
                const isSelected = selectedAnswer === i.toString();
                
                // Color formatting
                let btnStyle = "border-zinc-800 bg-zinc-950/20 text-zinc-300 hover:bg-zinc-900/40 hover:border-zinc-700";
                let icon = <HelpCircle className="h-5 w-5 text-zinc-600 shrink-0" />;

                if (answered) {
                  if (isSelected) {
                    if (resultCorrect === true) {
                      btnStyle = "border-emerald-500 bg-emerald-500/10 text-emerald-400";
                      icon = <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0" />;
                    } else if (resultCorrect === false) {
                      btnStyle = "border-red-500 bg-red-500/10 text-red-400";
                      icon = <XCircle className="h-5 w-5 text-red-400 shrink-0" />;
                    } else {
                      // answer submitted but result response pending
                      btnStyle = "border-indigo-500 bg-indigo-500/10 text-indigo-400";
                      icon = <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent shrink-0"></div>;
                    }
                  } else {
                    btnStyle = "border-zinc-900 bg-zinc-950/10 text-zinc-600 opacity-60";
                  }
                }

                return (
                  <button
                    key={i}
                    disabled={answered}
                    onClick={() => handleSelectOption(i)}
                    className={`glass-panel-interactive flex items-center justify-between p-5 rounded-xl border text-sm sm:text-base font-semibold transition-all cursor-pointer ${btnStyle}`}
                  >
                    <span>{opt}</span>
                    {icon}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
            <p className="text-zinc-500 text-sm">Esperando pregunta del servidor...</p>
          </div>
        )}
      </main>
    </div>
  );
}
