// SecurityScore.jsx
import { motion } from "framer-motion";

/**
 * summary: {
 *   score, finalEncryption, totalTimeSeconds,
 *   totalLatencyMs, latencyScore,
 *   stepDurations: [{ step, title, ms }]  // computed client-side from step timestamps
 * } | null
 * Only populated once Step 8 completes.
 */
export default function SecurityScore({ summary }) {
  if (!summary) {
    return (
      <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">
        <p className="text-[10px] font-mono tracking-wider text-white/30">SECURITY SCORE</p>
        <p className="mt-2 text-3xl font-mono text-white/15">--/100</p>
      </div>
    );
  }

  const {
    score,
    finalEncryption,
    totalTimeSeconds,
    totalLatencyMs,
    latencyScore,
    stepDurations,
  } = summary;
  const scoreColor = score >= 90 ? "text-emerald-400" : score >= 70 ? "text-amber-400" : "text-red-400";
  const latColor =
    latencyScore == null
      ? "text-white/30"
      : latencyScore >= 90
      ? "text-emerald-400"
      : latencyScore >= 60
      ? "text-amber-400"
      : "text-red-400";

  const maxDuration = stepDurations?.length
    ? Math.max(...stepDurations.map((d) => d.ms), 1)
    : 1;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-md bg-[#0b0f14] border border-white/5 p-5 space-y-4"
    >
      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">SECURITY SCORE</p>
        <p className={`mt-1 text-4xl font-mono font-semibold ${scoreColor}`}>
          {score}
          <span className="text-base text-white/30">/100</span>
        </p>
      </div>

      <div className="h-px bg-white/5" />

      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">FINAL ENCRYPTION</p>
        <p className="mt-1 text-sm text-white/90">{finalEncryption}</p>
      </div>

      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">TOTAL TIME</p>
        <p className="mt-1 font-mono text-sm text-cyan-400">{totalTimeSeconds}s</p>
      </div>

      {totalLatencyMs != null && (
        <>
          <div className="h-px bg-white/5" />
          <div>
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-mono tracking-wider text-white/30">LATENCY</p>
              {latencyScore != null && (
                <span className={`text-[10px] font-mono ${latColor}`}>{latencyScore}/100</span>
              )}
            </div>
            <p className="mt-1 font-mono text-sm text-white/70">{totalLatencyMs}ms</p>
          </div>
        </>
      )}

      {stepDurations?.length > 0 && (
        <>
          <div className="h-px bg-white/5" />
          <div>
            <p className="text-[10px] font-mono tracking-wider text-white/30 mb-2">
              PER-STEP BREAKDOWN
            </p>
            <div className="space-y-1.5">
              {stepDurations.map((d) => (
                <div key={d.step} className="flex items-center gap-2">
                  <span className="text-[9px] font-mono text-white/25 w-4 flex-shrink-0">
                    {String(d.step).padStart(2, "0")}
                  </span>
                  <div className="h-1.5 flex-1 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-cyan-400/60"
                      style={{ width: `${(d.ms / maxDuration) * 100}%` }}
                    />
                  </div>
                  <span className="text-[9px] font-mono text-white/40 w-12 text-right flex-shrink-0">
                    {d.ms.toFixed(0)}ms
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
}