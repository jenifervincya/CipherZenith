// Dashboard.jsx
import { useEffect, useRef, useState } from "react";
import StepFlow from "../components/StepFlow";
import TransactionPanel from "../components/TransactionPanel";
import SecurityScore from "../components/SecurityScore";
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

    setStepStates((prev) => ({
      ...prev,
      [msg.step]: { status: msg.status, details: msg.details, timestamp: msg.timestamp },
    }));

    if (msg.step === 8 && msg.status === "complete") {
      setSummary({
        score: msg.details.security_score ?? msg.details.score,
        finalEncryption: msg.details.final_encryption ?? msg.details.finalEncryption,
        totalTimeSeconds: msg.details.total_time ?? msg.details.totalTimeSeconds,
      });
    }
  }

  return (
    <div className="min-h-screen bg-[#05070a] text-white/90">
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <h1 className="text-lg font-semibold tracking-tight">CipherZenith</h1>
          <span className="text-xs font-mono text-white/30">Control Center</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[connStatus]}`} />
          <span className="text-xs font-mono text-white/40 uppercase">{connStatus}</span>
        </div>
      </header>

      <main className="p-6 grid grid-cols-1 lg:grid-cols-[240px_1fr_240px] gap-4">
        <TransactionPanel transaction={transaction} />

        <section>
          <p className="text-[10px] font-mono tracking-wider text-white/30 mb-3">
            SECURITY PIPELINE — 8 STEPS
          </p>
          <StepFlow stepStates={stepStates} />
        </section>

        <SecurityScore summary={summary} />
      </main>
    </div>
  );
}