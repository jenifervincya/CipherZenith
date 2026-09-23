// stepExplainers.js
// Static "what's actually happening under the hood" text for each of the
// 8 pipeline steps. Shown when a judge clicks a step card to expand it.
// This is explanatory/demo content, not derived from live backend data.

export const STEP_EXPLAINERS = {
  1: {
    tagline: "The entry point — nothing is secured yet, just logged.",
    body: "The backend receives the raw transaction request, assigns it a unique ID, and timestamps it. This is the baseline record everything downstream attaches to.",
    underTheHood: [
      "Transaction ID generated (UUID-based)",
      "Sender, receiver, amount captured from the request body",
      "Broadcast to the dashboard begins here — every later step references this same ID",
    ],
  },
  2: {
    tagline: "Two independent locks, applied together.",
    body: "The transaction payload is encrypted with AES-256 (classical, fast, battle-tested) and the AES key itself is wrapped using Kyber512 (post-quantum key encapsulation). An attacker needs to break both to read the data.",
    underTheHood: [
      "AES-256 encrypts the transaction payload",
      "Kyber512 encapsulates the AES key — this is the quantum-resistant layer",
      "Defends specifically against 'harvest now, decrypt later' attacks",
    ],
  },
  3: {
    tagline: "Does this transaction feel unusual?",
    body: "A model scores the transaction against typical behavior for this user — amount patterns, timing, frequency — and outputs a continuous anomaly score rather than a binary flag.",
    underTheHood: [
      "Anomaly score (0.0–1.0) from behavioral pattern comparison",
      "Risk level bucketed as LOW / MEDIUM / HIGH",
      "Feeds directly into the Adaptive Engine's decision (step 5)",
    ],
  },
  4: {
    tagline: "Does this match a known attack signature?",
    body: "Separate from step 3's behavioral scoring, this step checks for specific known attack patterns — replayed requests, man-in-the-middle indicators, velocity abuse.",
    underTheHood: [
      "Signature-based checks: replay attack, MITM pattern, velocity limit",
      "Outputs a confidence score alongside the threat type",
      "A positive detection here is what triggers Self-Healing (step 6)",
    ],
  },
  5: {
    tagline: "The decision-maker — escalate or hold steady.",
    body: "Combines the risk level from step 3 and the threat result from step 4 into one decision: keep current encryption, or switch to a stronger post-quantum configuration.",
    underTheHood: [
      "LOW risk, no threat → maintain AES-256 + Kyber512",
      "HIGH risk or confirmed threat → escalate to Kyber1024 (full PQC)",
      "This is the crypto-agility in action — the algorithm choice is runtime, not fixed",
    ],
  },
  6: {
    tagline: "Fixes itself — no human in the loop.",
    body: "If a threat was found, the system reacts automatically: rotating encryption keys so anything already captured becomes useless, and isolating the suspicious element from the rest of the flow.",
    underTheHood: [
      "Key rotation invalidates any previously intercepted key material",
      "Threat isolation — the suspicious request is contained, not just flagged",
      "Runs even when no threat is found, confirming system integrity either way",
    ],
  },
  7: {
    tagline: "One package split across three independent paths.",
    body: "The encrypted payload is fragmented and sent across three simulated transmission paths. An attacker capturing one path only gets a useless fragment.",
    underTheHood: [
      "3-way fragmentation of the encrypted payload",
      "Each fragment routed independently (simulated for this demo)",
      "All three must arrive for reassembly — no single point of interception is sufficient",
    ],
  },
  8: {
    tagline: "Reassembled, delivered, scored.",
    body: "Fragments are reassembled, the transaction is marked complete, and a final security score is computed from how the previous 7 steps went. The app only ever sees this end result.",
    underTheHood: [
      "Fragment reassembly and integrity check",
      "Security score computed from the full pipeline's outcome",
      "CipherPay app receives only 'Transaction Secured' — none of steps 1–7 are ever shown to the end user",
    ],
  },
};