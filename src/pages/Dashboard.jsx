// Dashboard.jsx
import { useEffect, useRef, useState } from "react";
import StepFlow, { STEP_DEFINITIONS } from "../components/StepFlow";
import TransactionPanel from "../components/TransactionPanel";
import SecurityScore from "../components/SecurityScore";
import CryptoExplorer from "../components/CryptoExplorer";
import { connectDashboardSocket } from "../services/websocket";
import { assertCanConnectDashboard } from "../../security/auth_guard";

const STATUS_DOT = {
  connected: "bg-emerald-400",
  connecting: "bg-amber-400 animate-pulse",
  disconnected: "bg-red-500",
  error: "bg-red-500",
};

export default function Dashboard() {
  const [connStatus, setConnStatus] = useState("connecting");
  const [transaction, setTransaction] = useState(null);
  const [stepStates, setStepStates] = useState({});
  const [summary, setSummary] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    try {
      assertCanConnectDashboard();
    } catch (err) {
      console.error(err);
      setConnStatus("error");
      return;
    }

    socketRef.current = connectDashboardSocket({
      onOpen: () => setConnStatus("connected"),
      onClose: () => setConnStatus("disconnected"),
      onError: () => setConnStatus("error"),
      onStepUpdate: (msg) => handleStepUpdate(msg),
    });

    return () => socketRef.current?.close();
  }, []);

  function handleStepUpdate(msg) {
    // Step 1 also carries the transaction header info
    if (msg.step === 1) {
      setTransaction({
        id: msg.details.transaction_id ?? msg.details.id,
        sender: msg.details.sender,
        receiver: msg.details.receiver,
        amount: msg.details.amount,
        timestamp: msg.timestamp,
      });
      // fresh transaction — reset the flow
      setStepStates({});
      setSummary(null);
    }

    setStepStates((prev) => {
      const next = {
        ...prev,
        [msg.step]: { status: msg.status, details: msg.details, timestamp: msg.timestamp },
      };

      if (msg.step === 8 && msg.status === "complete") {
        setSummary({
          score: msg.details.security_score ?? msg.details.score,
          finalEncryption: msg.details.final_encryption ?? msg.details.finalEncryption,
          totalTimeSeconds: msg.details.total_time ?? msg.details.totalTimeSeconds,
          totalLatencyMs: msg.details.total_latency_ms ?? null,
          latencyScore: msg.details.latency_score ?? null,
          stepDurations: computeStepDurations(next),
        });
      }

      return next;
    });
  }

  return (
    <div className="min-h-screen bg-[#05070a] text-white/90">
      <header className="border-b border-white/5 px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 sm:gap-3">
          <img
            src="/cipherpay-logo.png"
            alt="CipherPay"
            className="h-7 w-7 sm:h-8 sm:w-8 rounded-md flex-shrink-0"
          />
          <div className="flex items-baseline gap-2 sm:gap-3">
            <h1 className="text-base sm:text-lg font-semibold tracking-tight">CipherZenith</h1>
            <span className="text-[10px] sm:text-xs font-mono text-white/30">Dashboard</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[connStatus]}`} />
          <span className="text-[10px] sm:text-xs font-mono text-white/40 uppercase">{connStatus}</span>
        </div>
      </header>

      <main className="p-3 sm:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_240px] gap-3 sm:gap-4">
          <TransactionPanel transaction={transaction} />

          <section>
            <p className="text-[10px] font-mono tracking-wider text-white/30 mb-3">
              SECURITY PIPELINE — 8 STEPS &nbsp;
              <span className="text-white/15">(click a step to explore)</span>
            </p>
            <StepFlow stepStates={stepStates} />
          </section>

          <SecurityScore summary={summary} />
        </div>

        <CryptoExplorer />
      </main>
    </div>
  );
}

/**
 * Computes a per-step duration breakdown purely from the timestamps
 * already carried on every WebSocket message — no backend change needed
 * for this part. Each step's duration = its own timestamp minus the
 * previous step's timestamp (step 1's duration is omitted, since there's
 * no prior step to measure against on the client).
 */
function computeStepDurations(stepStates) {
  const ordered = STEP_DEFINITIONS
    .map(({ step, title }) => ({ step, title, ts: stepStates[step]?.timestamp }))
    .filter((s) => s.ts);

  const durations = [];
  for (let i = 1; i < ordered.length; i++) {
    const prev = new Date(ordered[i - 1].ts).getTime();
    const curr = new Date(ordered[i].ts).getTime();
    const ms = curr - prev;
    if (Number.isFinite(ms) && ms >= 0) {
      durations.push({ step: ordered[i].step, title: ordered[i].title, ms });
    }
  }
  return durations;
}