// SecurityScore.jsx
import { motion } from "framer-motion";

/**
 * summary: { score, finalEncryption, totalTimeSeconds } | null
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

  const { score, finalEncryption, totalTimeSeconds } = summary;
  const scoreColor = score >= 90 ? "text-emerald-400" : score >= 70 ? "text-amber-400" : "text-red-400";

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
    </motion.div>
  );
}