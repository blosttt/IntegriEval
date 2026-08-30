"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { api, getWsBase } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────
interface SessionInfo {
  session_id: number;
  student_name: string;
  evaluation_title: string;
  total_questions: number;
  time_per_question: number;
}

interface Question {
  question_id: number;
  text: string;
  q_type: "multiple_choice" | "true_false";
  options: string[];
  index: number;
  total: number;
  limit_seconds: number;
}

type Phase =
  | "loading"
  | "error"
  | "ready"
  | "in_progress"
  | "finished"
  | "already_done";

// ── Component ─────────────────────────────────────────────────────────────────
export default function FlashTestPage() {
  const { token } = useParams<{ token: string }>();

  // Meta
  const [phase, setPhase] = useState<Phase>("loading");
  const [errorMsg, setErrorMsg] = useState("");
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);

  // Test state
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<boolean | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [score, setScore] = useState<{
    score: number;
    percentage_score: number;
    classification: string;
  } | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── 1. Validate token ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!token) return;
    api
      .validateFlashToken(token)
      .then((info: SessionInfo) => {
        setSessionInfo(info);
        setPhase("ready");
      })
      .catch((err: Error) => {
        const msg = err.message || "";
        if (msg.includes("ya completaste") || msg.includes("ya completaste")) {
          setPhase("already_done");
        } else {
          setErrorMsg(msg);
          setPhase("error");
        }
      });
  }, [token]);

  // ── 2. Start WebSocket ──────────────────────────────────────────────────────
  function startTest() {
    if (!sessionInfo) return;
    const wsUrl = `${getWsBase()}/flash/ws/${sessionInfo.session_id}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setPhase("in_progress");

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "question") {
        clearTimer();
        setLastResult(null);
        setSelectedAnswer(null);
        setCurrentQuestion(msg as Question);
        setTimeLeft(msg.limit_seconds);
        startTimer(msg.limit_seconds, () => {
          // Auto-send null answer on timeout
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(
              JSON.stringify({
                action: "answer",
                question_id: msg.question_id,
                answer: null,
              })
            );
          }
        });
      }

      if (msg.type === "result") {
        clearTimer();
        setLastResult(msg.is_correct);
      }

      if (msg.type === "timeout") {
        clearTimer();
        setLastResult(false);
      }

      if (msg.type === "finished") {
        clearTimer();
        setScore({
          score: msg.score,
          percentage_score: msg.percentage_score,
          classification: msg.classification,
        });
        setPhase("finished");
        ws.close();
      }
    };

    ws.onerror = () => {
      setErrorMsg("Error de conexión. Por favor recarga la página e intenta de nuevo.");
      setPhase("error");
    };
    ws.onclose = () => clearTimer();
  }

  // ── Timer helpers ──────────────────────────────────────────────────────────
  function startTimer(seconds: number, onExpire: () => void) {
    setTimeLeft(seconds);
    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearTimer();
          onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }

  function clearTimer() {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  // ── Answer submission ──────────────────────────────────────────────────────
  function submitAnswer(answer: string) {
    if (!currentQuestion || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;
    setSelectedAnswer(answer);
    clearTimer();
    wsRef.current.send(
      JSON.stringify({
        action: "answer",
        question_id: currentQuestion.question_id,
        answer,
      })
    );
  }

  // ── Cleanup ────────────────────────────────────────────────────────────────
  useEffect(() => {
    return () => {
      clearTimer();
      wsRef.current?.close();
    };
  }, []);

  // ── Render ─────────────────────────────────────────────────────────────────
  if (phase === "loading") {
    return <Screen><Spinner text="Verificando tu enlace…" /></Screen>;
  }

  if (phase === "error") {
    return (
      <Screen>
        <div className="text-center space-y-4">
          <div className="text-6xl">⚠️</div>
          <h1 className="text-2xl font-bold text-red-400">Enlace inválido</h1>
          <p className="text-gray-400 max-w-md">{errorMsg}</p>
        </div>
      </Screen>
    );
  }

  if (phase === "already_done") {
    return (
      <Screen>
        <div className="text-center space-y-4">
          <div className="text-6xl">✅</div>
          <h1 className="text-2xl font-bold text-green-400">Ya completaste este test</h1>
          <p className="text-gray-400">Tu respuesta ha sido registrada. Puedes cerrar esta ventana.</p>
        </div>
      </Screen>
    );
  }

  if (phase === "ready" && sessionInfo) {
    return (
      <Screen>
        <div className="text-center space-y-6 max-w-xl">
          <div className="text-5xl">📝</div>
          <h1 className="text-3xl font-bold text-white">Flash Test</h1>
          <p className="text-indigo-300 text-lg font-medium">{sessionInfo.evaluation_title}</p>
          <div className="bg-gray-800 rounded-xl p-6 text-left space-y-3">
            <p className="text-gray-300">
              Hola <span className="font-semibold text-white">{sessionInfo.student_name}</span>, debes responder:
            </p>
            <ul className="text-gray-400 space-y-1 text-sm list-disc list-inside">
              <li><span className="text-white font-medium">{sessionInfo.total_questions} preguntas</span> sobre tu trabajo</li>
              <li>
                <span className="text-white font-medium">{sessionInfo.time_per_question} segundos</span> por pregunta
              </li>
              <li>No puedes pausar el test una vez iniciado</li>
              <li>Responde según lo que escribiste en tu informe</li>
            </ul>
          </div>
          <button
            onClick={startTest}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 px-8 rounded-xl text-lg transition-colors"
          >
            Comenzar Flash Test →
          </button>
        </div>
      </Screen>
    );
  }

  if (phase === "in_progress" && currentQuestion) {
    const timerPct = (timeLeft / currentQuestion.limit_seconds) * 100;
    const timerColor =
      timerPct > 50 ? "bg-green-500" : timerPct > 25 ? "bg-yellow-500" : "bg-red-500";

    return (
      <Screen>
        <div className="w-full max-w-2xl space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Pregunta {currentQuestion.index + 1} de {currentQuestion.total}</span>
            <span
              className={`font-bold text-lg ${
                timeLeft <= 10 ? "text-red-400 animate-pulse" : "text-white"
              }`}
            >
              {timeLeft}s
            </span>
          </div>

          {/* Timer bar */}
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-1000 ${timerColor}`}
              style={{ width: `${timerPct}%` }}
            />
          </div>

          {/* Result flash */}
          {lastResult !== null && (
            <div
              className={`text-center py-3 rounded-lg font-bold text-lg ${
                lastResult
                  ? "bg-green-900 text-green-300"
                  : "bg-red-900 text-red-300"
              }`}
            >
              {lastResult ? "✅ Correcto" : "❌ Incorrecto"}
            </div>
          )}

          {/* Question */}
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-white text-lg leading-relaxed">{currentQuestion.text}</p>
          </div>

          {/* Options */}
          <div className="grid gap-3">
            {currentQuestion.options?.map((opt, idx) => {
              const idxStr = String(idx);
              const isSelected = selectedAnswer === idxStr;
              return (
                <button
                  key={idx}
                  disabled={selectedAnswer !== null}
                  onClick={() => submitAnswer(idxStr)}
                  className={`w-full text-left px-5 py-4 rounded-xl font-medium transition-all border ${
                    isSelected
                      ? "border-indigo-500 bg-indigo-900 text-indigo-200"
                      : "border-gray-600 bg-gray-800 text-gray-200 hover:border-indigo-400 hover:bg-gray-700"
                  } disabled:cursor-default`}
                >
                  <span className="text-gray-500 mr-3">{String.fromCharCode(65 + idx)}.</span>
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      </Screen>
    );
  }

  if (phase === "in_progress" && !currentQuestion) {
    return <Screen><Spinner text="Cargando pregunta…" /></Screen>;
  }

  if (phase === "finished" && score) {
    const pct = Math.round(score.percentage_score * 100);
    const classLabel: Record<string, string> = {
      low: "Resultado bajo",
      medium: "Resultado medio",
      high: "Resultado excelente",
    };
    const classColor: Record<string, string> = {
      low: "text-red-400",
      medium: "text-yellow-400",
      high: "text-green-400",
    };

    return (
      <Screen>
        <div className="text-center space-y-6 max-w-md">
          <div className="text-6xl">{pct >= 70 ? "🎉" : pct >= 50 ? "📊" : "😔"}</div>
          <h1 className="text-3xl font-bold text-white">Flash Test Completado</h1>
          <div className="bg-gray-800 rounded-xl p-8 space-y-4">
            <div>
              <p className="text-gray-400 text-sm">Tu resultado</p>
              <p className="text-5xl font-bold text-white mt-1">{pct}%</p>
            </div>
            <p className={`font-semibold text-lg ${classColor[score.classification]}`}>
              {classLabel[score.classification]}
            </p>
          </div>
          <p className="text-gray-400 text-sm">
            Tu resultado ha sido registrado. Si recibes un correo adicional con una cita,
            tu profesor quiere conversar contigo sobre tu trabajo.
          </p>
          <p className="text-gray-500 text-sm">Puedes cerrar esta ventana.</p>
        </div>
      </Screen>
    );
  }

  return null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function Screen({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
      {children}
    </div>
  );
}

function Spinner({ text }: { text: string }) {
  return (
    <div className="text-center space-y-4">
      <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-gray-400">{text}</p>
    </div>
  );
}
