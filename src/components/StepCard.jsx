// StepCard.jsx
import { motion, AnimatePresence } from "framer-motion";

const STATUS_STYLES = {
  idle: {
    ring: "ring-1 ring-white/10",
    dot: "bg-white/20",
    label: "IDLE",
    labelColor: "text-white/30",
  },
  processing: {
    ring: "ring-1 ring-cyan-400/60",
    dot: "bg-cyan-400",
    label: "PROCESSING",
    labelColor: "text-cyan-400",
  },
  complete: {
    ring: "ring-1 ring-emerald-400/50",
    dot: "bg-emerald-400",
    label: "COMPLETE",
    labelColor: "text-emerald-400",
  },
  threat_detected: {
    ring: "ring-1 ring-red-500/70",
    dot: "bg-red-500",
    label: "ALERT",
    labelColor: "text-red-400",
  },
};

/**
 * Renders one of the 8 security step cards.
 * status: "idle" | "processing" | "complete" | "threat_detected"
 * details: arbitrary key/value pairs to render (from backend WS message)
 */
export default function StepCard({ index, title, status = "idle", details = {}, timestamp }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.idle;
  const isActive = status === "processing";
  const isThreat = status === "threat_detected";

  return (
    <motion.div
      layout
      className={`relative overflow-hidden rounded-md bg-[#0b0f14] border border-white/5 ${style.ring} p-4`}
      animate={isThreat ? { x: [0, -4, 4, -4, 0] } : {}}
      transition={{ duration: 0.4 }}
    >
      {/* scanline sweep while processing — the signature motion element */}
      {isActive && (
        <motion.div
          className="pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent"
          animate={{ x: ["-100%", "300%"] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
        />
      )}

      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-white/30">
            {String(index).padStart(2, "0")}
          </span>
          <h3 className="text-sm font-semibold text-white/90">{title}</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`h-1.5 w-1.5 rounded-full ${style.dot} ${
              isActive ? "animate-pulse" : ""
            }`}
          />
          <span className={`font-mono text-[10px] tracking-wider ${style.labelColor}`}>
            {style.label}
          </span>
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={status}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="mt-3 space-y-1"
        >
          {Object.entries(details).map(([key, value]) => (
            <DetailRow key={key} label={key} value={value} isThreat={isThreat} />
          ))}
        </motion.div>
      </AnimatePresence>

      {timestamp && (
        <div className="mt-3 font-mono text-[10px] text-white/20">{timestamp}</div>
      )}
    </motion.div>
  );
}

function DetailRow({ label, value, isThreat }) {
  const displayLabel = label.replace(/_/g, " ");

  // Render numeric 0-1 scores as a small progress bar (e.g. anomaly_score)
  if (typeof value === "number" && value >= 0 && value <= 1 && /score/i.test(label)) {
    return (
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="text-white/40 capitalize">{displayLabel}</span>
        <div className="flex items-center gap-2 w-28">
          <div className="h-1 flex-1 rounded-full bg-white/10 overflow-hidden">
            <div
              className={`h-full rounded-full ${isThreat ? "bg-red-500" : "bg-cyan-400"}`}
              style={{ width: `${value * 100}%` }}
            />
          </div>
          <span className="font-mono text-white/60">{value.toFixed(2)}</span>
        </div>
      </div>
    );
  }

  const stringValue = String(value);
  const isLong = stringValue.length > 16;

  if (isLong) {
    return (
      <div className="text-xs">
        <span className="text-white/40 capitalize">{displayLabel}</span>
        <div className={`font-mono mt-0.5 ${isThreat ? "text-red-400" : "text-white/70"}`}>
          {stringValue}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-white/40 capitalize">{displayLabel}</span>
      <span className={`font-mono ${isThreat ? "text-red-400" : "text-white/70"}`}>
        {stringValue}
      </span>
    </div>
  );
}