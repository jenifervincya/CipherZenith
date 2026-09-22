// CryptoExplorer.jsx
// Simulated view of CipherZenith's adaptive encryption architecture:
//
// LOW    = AES-256-GCM only
// MEDIUM = Kyber512 + AES-256-GCM
// HIGH   = Kyber1024 only
//
// Demo/concept only — not wired to real crypto or live transaction data.

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

// ---------------------------------------------------------------------
// Shared fake-data helpers
// ---------------------------------------------------------------------

function randomHex(bytes) {
  let s = "";

  for (let i = 0; i < bytes; i++) {
    s += Math.floor(Math.random() * 256)
      .toString(16)
      .padStart(2, "0");
  }

  return s;
}

// ---------------------------------------------------------------------
// Risk tiers
// ---------------------------------------------------------------------

const TIERS = {
  LOW: {
    algo: "AES-256-GCM",
    label: "AES-256-GCM",
    pubKeyBytes: null,
    ctBytes: null,
    speed: "Fastest",
    usesKyber: false,
    usesAES: true,
  },

  MEDIUM: {
    algo: "Kyber512 + AES-256-GCM",
    label: "KYBER512-AES256GCM",
    pubKeyBytes: 800,
    ctBytes: 768,
    speed: "Faster",
    usesKyber: true,
    usesAES: true,
  },

  HIGH: {
    algo: "Kyber1024",
    label: "KYBER1024",
    pubKeyBytes: 1568,
    ctBytes: 1568,
    speed: "Stronger",
    usesKyber: true,
    usesAES: false,
  },
};

// ---------------------------------------------------------------------
// Panel 1 — Encryption sequence
// ---------------------------------------------------------------------
//
// LOW:
//   Session ready
//   AES-256-GCM Encrypt
//
// MEDIUM:
//   Session ready
//   Kyber512 Encapsulate
//   Derive AES key
//   AES-256-GCM Encrypt
//
// HIGH:
//   Session ready
//   Kyber1024 Encapsulate
//
// ---------------------------------------------------------------------

function getStages(tier) {
  // --------------------------------------------------
  // LOW — AES-256-GCM only
  // --------------------------------------------------

  if (tier === "LOW") {
    return {
      sender: [
        {
          id: "keypair",
          label: "Session ready",
          sublabel: "Transaction payload prepared",
          duration: 350,
        },

        {
          id: "encrypt",
          label: "AES-256-GCM Encrypt",
          sublabel: "Payload + random nonce",
          duration: 450,
        },
      ],

      receiver: [
        {
          id: "holds",
          label: "Holds AES key",
          sublabel: "Symmetric key",
          duration: 350,
        },

        {
          id: "decrypt",
          label: "AES-256-GCM Decrypt",
          sublabel: "Recovers original transaction JSON",
          duration: 450,
        },
      ],
    };
  }

  // --------------------------------------------------
  // MEDIUM — Kyber512 + AES-256-GCM
  // --------------------------------------------------

  if (tier === "MEDIUM") {
    return {
      sender: [
        {
          id: "keypair",
          label: "Session ready",
          sublabel: "Transaction payload prepared",
          duration: 350,
        },

        {
          id: "encapsulate",
          label: "Kyber512 Encapsulate",
          sublabel: "Against receiver's Kyber512 public key",
          duration: 650,
        },

        {
          id: "derive-s",
          label: "Derive AES key",
          sublabel: "SHA-256(shared secret)",
          duration: 350,
        },

        {
          id: "encrypt",
          label: "AES-256-GCM Encrypt",
          sublabel: "Payload + random nonce",
          duration: 450,
        },
      ],

      receiver: [
        {
          id: "holds",
          label: "Holds Kyber512 keypair",
          sublabel: "Kyber512 public/private key",
          duration: 350,
        },

        {
          id: "decapsulate",
          label: "Kyber512 Decapsulate",
          sublabel: "Recovers shared secret via private key",
          duration: 650,
        },

        {
          id: "derive-r",
          label: "Derive AES key",
          sublabel: "Same SHA-256 process — keys match",
          duration: 350,
        },

        {
          id: "decrypt",
          label: "AES-256-GCM Decrypt",
          sublabel: "Recovers original transaction JSON",
          duration: 450,
        },
      ],
    };
  }

  // --------------------------------------------------
  // HIGH — Kyber1024 only
  // --------------------------------------------------

  if (tier === "HIGH") {
    return {
      sender: [
        {
          id: "keypair",
          label: "Session ready",
          sublabel: "Transaction payload prepared",
          duration: 350,
        },

        {
          id: "encapsulate",
          label: "Kyber1024 Encapsulate",
          sublabel: "Against receiver's Kyber1024 public key",
          duration: 900,
        },
      ],

      receiver: [
        {
          id: "holds",
          label: "Holds Kyber1024 keypair",
          sublabel: "Kyber1024 public/private key",
          duration: 350,
        },

        {
          id: "decapsulate",
          label: "Kyber1024 Decapsulate",
          sublabel: "Recovers shared secret via private key",
          duration: 900,
        },
      ],
    };
  }

  // Fallback
  return {
    sender: [],
    receiver: [],
  };
}

// ---------------------------------------------------------------------
// Panel 1 — Encryption Sequence
// ---------------------------------------------------------------------

function EncryptionSequence({ tier, setTier, onResult }) {
  const [running, setRunning] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [completedIdx, setCompletedIdx] = useState(-1);

  const timeouts = useRef([]);

  const { sender: senderStages, receiver: receiverStages } =
    getStages(tier);

  const tierConfig = TIERS[tier];

  // --------------------------------------------------
  // Reset
  // --------------------------------------------------

  function reset() {
    timeouts.current.forEach(clearTimeout);
    timeouts.current = [];

    setRunning(false);
    setActiveIdx(-1);
    setCompletedIdx(-1);

    onResult(null);
  }

  // --------------------------------------------------
  // Run encryption
  // --------------------------------------------------

  function run() {
    reset();

    setRunning(true);

    let elapsed = 0;

    const stages = getStages(tier).sender;

    stages.forEach((stage, i) => {
      // Activate current stage
      timeouts.current.push(
        setTimeout(() => {
          setActiveIdx(i);
        }, elapsed)
      );

      elapsed += stage.duration;

      // Complete current stage
      timeouts.current.push(
        setTimeout(() => {
          setCompletedIdx(i);

          if (i === stages.length - 1) {
            setActiveIdx(-1);
            setRunning(false);

            const t = TIERS[tier];

            onResult({
              tier,

              algorithm_label: t.label,
              algorithm: t.algo,

              usesKyber: t.usesKyber,
              usesAES: t.usesAES,

              // Kyber ciphertext exists for MEDIUM and HIGH
              kyberCiphertext: t.usesKyber
                ? randomHex(20) + `… (${t.ctBytes}B)`
                : null,

              // AES fields only exist for LOW and MEDIUM
              aesNonce: t.usesAES
                ? randomHex(12)
                : null,

              aesCiphertext: t.usesAES
                ? randomHex(24) + "…"
                : null,

              totalMs: elapsed,

              securityNote:
                tier === "HIGH"
                  ? "Kyber1024 private key remains uncompromised"
                  : tier === "MEDIUM"
                    ? "Kyber512 private key remains uncompromised"
                    : "AES-256-GCM key remains uncompromised",
            });
          }
        }, elapsed)
      );
    });
  }

  // --------------------------------------------------
  // Cleanup
  // --------------------------------------------------

  useEffect(() => {
    return () => {
      timeouts.current.forEach(clearTimeout);
    };
  }, []);

  // Reset whenever tier changes
  useEffect(() => {
    reset();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tier]);

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="h-2 w-2 rounded-full bg-cyan-400" />

        <p className="text-[10px] font-mono tracking-wider text-white/30">
          ENCRYPTION SEQUENCE
        </p>
      </div>

      {/* Tier Selector */}
      <div className="flex gap-1.5 mb-4">
        {Object.keys(TIERS).map((t) => (
          <button
            key={t}
            onClick={() => setTier(t)}
            disabled={running}
            className={`flex-1 px-2 py-1 rounded text-[10px] font-mono border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
              tier === t
                ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-400"
                : "border-white/10 text-white/40 hover:bg-white/5"
            }`}
          >
            {t} TIER
          </button>
        ))}
      </div>

      {/* Sender / Receiver Labels */}
      <div className="grid grid-cols-2 gap-3 mb-2">
        <p className="text-[10px] font-mono tracking-wider text-white/30 text-center">
          SENDER
        </p>

        <p className="text-[10px] font-mono tracking-wider text-white/30 text-center">
          RECEIVER
        </p>
      </div>

      {/* Sender / Receiver Stages */}
      <div className="grid grid-cols-2 gap-3 mb-4">

        {/* Sender */}
        <div className="space-y-2">
          {senderStages.map((s, i) => (
            <LaneStage
              key={s.id}
              {...s}
              active={activeIdx === i}
              done={completedIdx >= i}
              color="blue"
            />
          ))}
        </div>

        {/* Receiver */}
        <div className="space-y-2">
          {receiverStages.map((s, i) => (
            <LaneStage
              key={s.id}
              {...s}
              active={activeIdx === i}
              done={completedIdx >= i}
              color="violet"
            />
          ))}
        </div>

      </div>

      {/* Controls */}
      <div className="flex gap-2 mb-4">

        <button
          onClick={run}
          disabled={running}
          className="px-3 py-1.5 rounded text-xs font-mono bg-cyan-400/10 text-cyan-400 border border-cyan-400/30 hover:bg-cyan-400/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {running ? "Encrypting…" : "Run encryption"}
        </button>

        <button
          onClick={reset}
          className="px-3 py-1.5 rounded text-xs font-mono bg-white/5 text-white/50 border border-white/10 hover:bg-white/10 transition-colors"
        >
          Reset
        </button>

      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mb-3">
        <LegendDot
          color="bg-blue-400"
          label="Sender operations"
        />

        <LegendDot
          color="bg-violet-400"
          label="Receiver operations"
        />

        <LegendDot
          color="bg-cyan-400"
          label="Shared key material"
        />
      </div>

      <div className="h-px bg-white/5 mb-3" />

      {/* Description */}
      <p className="text-[11px] text-white/40 leading-relaxed">

        {tier === "LOW" && (
          <>
            LOW-risk transactions use{" "}
            <b className="text-white/60">
              AES-256-GCM
            </b>{" "}
            directly for payload encryption without a Kyber KEM.
          </>
        )}

        {tier === "MEDIUM" && (
          <>
            MEDIUM-risk transactions use{" "}
            <b className="text-white/60">
              Kyber512
            </b>{" "}
            to establish shared key material, followed by{" "}
            <b className="text-white/60">
              AES-256-GCM
            </b>{" "}
            for transaction payload encryption.
          </>
        )}

        {tier === "HIGH" && (
          <>
            HIGH-risk transactions use{" "}
            <b className="text-white/60">
              Kyber1024
            </b>{" "}
            as the selected cryptographic mechanism. The HIGH tier does
            not execute an AES-256-GCM payload-encryption stage in this
            demonstration.
          </>
        )}

      </p>
    </div>
  );
}

// ---------------------------------------------------------------------
// Lane Stage
// ---------------------------------------------------------------------

function LaneStage({
  label,
  sublabel,
  active,
  done,
  color,
}) {
  const c =
    color === "blue"
      ? {
          ring: "ring-blue-400/50",
          dot: "bg-blue-400",
        }
      : {
          ring: "ring-violet-400/50",
          dot: "bg-violet-400",
        };

  return (
    <div
      className={`relative overflow-hidden rounded px-2.5 py-2 border transition-colors ${
        active
          ? `border-white/20 bg-white/[0.04] ring-1 ${c.ring}`
          : done
            ? "border-emerald-400/30 bg-emerald-400/[0.03]"
            : "border-white/5"
      }`}
    >

      {/* Animated active sweep */}
      {active && (
        <motion.div
          className="pointer-events-none absolute inset-y-0 left-0 w-1/2 bg-gradient-to-r from-transparent via-white/5 to-transparent"
          animate={{
            x: ["-100%", "300%"],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      )}

      <div className="flex items-center justify-between relative">

        <div className="min-w-0">
          <p className="text-[11px] font-medium text-white/85 truncate">
            {label}
          </p>

          <p className="text-[9px] font-mono text-white/25 truncate">
            {sublabel}
          </p>
        </div>

        <span
          className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ml-2 ${
            active
              ? `${c.dot} animate-pulse`
              : done
                ? "bg-emerald-400"
                : "bg-white/15"
          }`}
        />

      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Legend Dot
// ---------------------------------------------------------------------

function LegendDot({ color, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className={`h-1.5 w-1.5 rounded-full ${color}`}
      />

      <span className="text-[10px] text-white/40">
        {label}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------
// Panel 2 — Encryption Result
// ---------------------------------------------------------------------

function EncryptionResult({ result }) {
  return (
    <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="h-2 w-2 rounded-full bg-amber-400" />

        <p className="text-[10px] font-mono tracking-wider text-white/30">
          ENCRYPTION RESULT
        </p>
      </div>

      {!result ? (
        <p className="text-xs text-white/25 font-mono py-6 text-center">
          Run encryption to see the output
        </p>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3"
        >

          {/* Risk Tier */}
          <ResultRow
            label="Risk tier"
            value={result.tier}
            highlight
          />

          {/* Algorithm */}
          <ResultRow
            label="Algorithm"
            value={result.algorithm_label}
            highlight
          />

          {/* Kyber Ciphertext */}
          {result.kyberCiphertext && (
            <ResultRow
              label="Kyber ciphertext (kyber_ciphertext)"
              value={result.kyberCiphertext}
              mono
            />
          )}

          {/* AES Nonce */}
          {result.aesNonce && (
            <ResultRow
              label="AES nonce (aes_nonce)"
              value={result.aesNonce}
              mono
            />
          )}

          {/* AES Ciphertext */}
          {result.aesCiphertext && (
            <ResultRow
              label="AES ciphertext (aes_ciphertext)"
              value={result.aesCiphertext}
              mono
            />
          )}

          <div className="h-px bg-white/5" />

          {/* Total Time */}
          <ResultRow
            label="Total encryption time"
            value={`~${result.totalMs} ms (demo-scale)`}
          />

          {/* Security */}
          <ResultRow
            label="Security holds if…"
            value={result.securityNote}
            strong
          />

        </motion.div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------
// Result Row
// ---------------------------------------------------------------------

function ResultRow({
  label,
  value,
  mono,
  highlight,
  strong,
}) {
  return (
    <div className="flex items-start justify-between gap-3">

      <span className="text-[11px] text-white/40 flex-shrink-0">
        {label}
      </span>

      <span
        className={`text-[11px] text-right truncate ${
          mono ? "font-mono" : ""
        } ${
          highlight
            ? "text-cyan-400"
            : strong
              ? "text-white/80 font-medium"
              : "text-white/70"
        }`}
        title={value}
      >
        {value}
      </span>

    </div>
  );
}

// ---------------------------------------------------------------------
// Panel 3 — Latency under transaction load
// ---------------------------------------------------------------------

function baseLatency(mode, tps) {
  const load = tps / 1000;

  if (mode === "aes") {
    return 4 + load * 2;
  }

  if (mode === "k512") {
    return 11 + load * 5;
  }

  if (mode === "k1024") {
    return 19.5 + load * 8;
  }

  return 4 + load * 2;
}

// ---------------------------------------------------------------------
// Latency Panel
// ---------------------------------------------------------------------

function LatencyPanel({ tier }) {
  // --------------------------------------------------
  // Manual TPS only
  // No random jitter / setInterval
  // --------------------------------------------------

  const [tps, setTps] = useState(200);

  function handleSlider(e) {
    setTps(Number(e.target.value));
  }

  // --------------------------------------------------
  // Latency bars
  // --------------------------------------------------

  const bars = [
    {
      key: "aes",
      label: "AES256 (LOW tier)",
      color: "bg-emerald-400",
    },

    {
      key: "k512",
      label: "Kyber512 + AES256 (MEDIUM tier)",
      color: "bg-cyan-400",
    },

    {
      key: "k1024",
      label: "Kyber1024 (HIGH tier)",
      color: "bg-violet-400",
    },
  ].map((b) => ({
    ...b,
    ms: baseLatency(b.key, tps),
  }));

  const maxMs = Math.max(
    ...bars.map((b) => b.ms),
    1
  );

  const tierKeyMap = {
    LOW: "aes",
    MEDIUM: "k512",
    HIGH: "k1024",
  };

  return (
    <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">

        <span className="h-2 w-2 rounded-full bg-violet-400" />

        <p className="text-[10px] font-mono tracking-wider text-white/30">
          LATENCY UNDER TRANSACTION LOAD
        </p>

        <span className="text-[9px] font-mono text-white/20 ml-auto">
          manual simulation
        </span>

      </div>

      {/* Latency Bars */}
      <div className="space-y-3 mb-4">

        {bars.map((b) => (
          <div key={b.key}>

            <div className="flex items-center justify-between mb-1">

              <span
                className={`text-xs ${
                  tierKeyMap[tier] === b.key
                    ? "text-white/90"
                    : "text-white/60"
                }`}
              >
                {b.label}
              </span>

              <span className="text-xs font-mono text-white/50">
                {b.ms.toFixed(1)} ms
              </span>

            </div>

            <div className="h-2 rounded-full bg-white/5 overflow-hidden">

              <motion.div
                className={`h-full rounded-full ${b.color}`}
                animate={{
                  width: `${(b.ms / maxMs) * 100}%`,
                }}
                transition={{
                  duration: 0.4,
                  ease: "easeInOut",
                }}
              />

            </div>

          </div>
        ))}

      </div>

      {/* Manual TPS Slider */}
      <div className="mb-4">

        <div className="flex items-center justify-between mb-2">

          <label className="text-[10px] font-mono tracking-wider text-white/30">
            LOAD — {tps} TPS
          </label>

        </div>

        <input
          type="range"
          min={0}
          max={2000}
          step={50}
          value={tps}
          onChange={handleSlider}
          className="w-full accent-cyan-400"
        />

      </div>

      {/* Risk Tier Table */}
      <table className="w-full text-xs">

        <thead>
          <tr className="text-white/25 text-[9px] font-mono tracking-wider">

            <td className="py-1">
              RISK TIER
            </td>

            <td className="py-1">
              ALGORITHM
            </td>

            <td className="py-1">
              PUBLIC KEY
            </td>

          </tr>
        </thead>

        <tbody>

          {Object.entries(TIERS).map(([t, v]) => (
            <tr
              key={t}
              className={`border-t border-white/5 ${
                tier === t
                  ? "text-white/90"
                  : "text-white/30"
              }`}
            >

              <td className="py-1.5 font-mono">
                {t}
              </td>

              <td
                className={`py-1.5 font-mono ${
                  tier === t
                    ? "text-cyan-400"
                    : ""
                }`}
              >
                {v.algo}
              </td>

              <td className="py-1.5 font-mono">
                {v.pubKeyBytes
                  ? `${v.pubKeyBytes}B`
                  : "—"}
              </td>

            </tr>
          ))}

        </tbody>

      </table>

    </div>
  );
}

// ---------------------------------------------------------------------
// Panel 4 — "Why this is the novel part"
// ---------------------------------------------------------------------

function NoveltyExplainer() {
  const points = [
    {
      title: "Reactive, not static",

      body:
        "Most PQC evaluations stop at “does it work.” CipherZenith escalates mid-flight — the AI risk score and threat detector feed directly into which tier (AES-only, Kyber512, or Kyber1024) is used, per transaction.",
    },

    {
      title: "Cost scales with risk",

      body:
        "LOW-risk traffic uses AES-256-GCM only. MEDIUM-risk traffic adds Kyber512, while HIGH-risk traffic uses Kyber1024 in this demonstration. The cryptographic path therefore changes according to the selected risk tier.",
    },

    {
      title: "Fallback-safe by design",

      body:
        "hybrid_scheme.py runs identically whether liboqs is available (REAL mode) or not (FALLBACK mode with matching return shapes) — the rest of the pipeline never has to know which mode it's in.",
    },
  ];

  return (
    <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">

      {/* Header */}
      <div className="flex items-center gap-2 mb-4">

        <span className="h-2 w-2 rounded-full bg-emerald-400" />

        <p className="text-[10px] font-mono tracking-wider text-white/30">
          WHY THIS IS THE NOVEL PART
        </p>

      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

        {points.map((p) => (
          <div key={p.title}>

            <p className="text-xs font-semibold text-cyan-400 mb-1">
              {p.title}
            </p>

            <p className="text-[11px] text-white/50 leading-relaxed">
              {p.body}
            </p>

          </div>
        ))}

      </div>

    </div>
  );
}

// ---------------------------------------------------------------------
// Export — full section
// ---------------------------------------------------------------------

export default function CryptoExplorer() {
  const [tier, setTier] = useState("LOW");
  const [result, setResult] = useState(null);

  return (
    <section className="mt-8">

      {/* Section Header */}
      <div className="flex items-baseline gap-2 mb-3">

        <p className="text-[10px] font-mono tracking-wider text-white/30">
          CRYPTO DEEP DIVE — ADAPTIVE KYBER ENCRYPTION (DEMO)
        </p>

        <span className="text-[9px] font-mono text-white/20">
          simulated, not live
        </span>

      </div>

      {/* Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        <EncryptionSequence
          tier={tier}
          setTier={setTier}
          onResult={setResult}
        />

        <EncryptionResult
          result={result}
        />

        <LatencyPanel
          tier={tier}
        />

        <NoveltyExplainer />

      </div>

    </section>
  );
}