// mock_backend.js
// A throwaway fake backend — NOT part of the real CipherZenith backend.
// Run this locally to test the dashboard's WebSocket handling and
// animations before Jenifer's real FastAPI backend is ready.
//
// Setup:
//   npm install ws
//   node mock_backend.js
//
// Then open your dashboard at localhost:5173 — it will auto-connect to
// ws://localhost:8000/ws/dashboard and play through one demo transaction
// every 12 seconds, on loop.

import { WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8000, path: "/ws/dashboard" });

console.log("Mock CipherZenith backend running on ws://localhost:8000/ws/dashboard");

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function now() {
  return new Date().toISOString();
}

// Set to true to simulate the "threat detected" demo path instead of the
// clean path. Toggle this to test both scenarios in the dashboard.
const SIMULATE_THREAT = true;

async function runDemoTransaction(socket) {
  const txnId = `TXN-${Date.now()}`;

  const steps = [
    {
      step: 1,
      title: "Transaction Received",
      status: "complete",
      details: {
        transaction_id: txnId,
        sender: "Jeni",
        receiver: "Mugunthan",
        amount: 500,
      },
    },
    {
      step: 2,
      title: "Hybrid Encryption",
      status: "complete",
      details: { "AES-256": "Applied", Kyber512: "Applied", Mode: "Hybrid Encryption Active" },
    },
    {
      step: 3,
      title: "AI Monitoring",
      status: "complete",
      details: {
        anomaly_score: SIMULATE_THREAT ? 0.81 : 0.12,
        risk_level: SIMULATE_THREAT ? "HIGH" : "LOW",
        patterns_checked: 47,
      },
    },
    {
      step: 4,
      title: "Threat Detection",
      status: SIMULATE_THREAT ? "threat_detected" : "complete",
      details: SIMULATE_THREAT
        ? { threat_type: "Replay Attack", confidence: 0.87 }
        : { result: "No Threats Detected", confidence: 0.985 },
    },
    {
      step: 5,
      title: "Adaptive Engine",
      status: "complete",
      details: {
        risk_level: SIMULATE_THREAT ? "HIGH" : "LOW",
        decision: SIMULATE_THREAT ? "Switch Algorithm" : "Maintain",
        algorithm: SIMULATE_THREAT ? "Kyber1024" : "AES-256 + Kyber512",
      },
    },
    {
      step: 6,
      title: "Self Healing",
      status: "complete",
      details: {
        system_integrity: "Intact",
        key_rotation: SIMULATE_THREAT ? "Done" : "Not Needed",
        threat_isolation: SIMULATE_THREAT ? "Done" : "Not Needed",
      },
    },
    {
      step: 7,
      title: "Multi-path Transmission",
      status: "complete",
      details: {
        "Fragment 1 -> Path 1": "OK",
        "Fragment 2 -> Path 2": "OK",
        "Fragment 3 -> Path 3": "OK",
      },
    },
    {
      step: 8,
      title: "Secure Output",
      status: "complete",
      details: {
        security_score: SIMULATE_THREAT ? 91 : 97,
        final_encryption: SIMULATE_THREAT ? "Full PQC" : "Hybrid PQC",
        total_time: 1.2,
      },
    },
  ];

  for (const step of steps) {
    // send a "processing" flash first, then "complete" — mimics real timing
    if (step.status !== "threat_detected") {
      socket.send(
        JSON.stringify({ ...step, status: "processing", timestamp: now() })
      );
      await delay(500);
    }
    socket.send(JSON.stringify({ ...step, timestamp: now() }));
    await delay(900);
  }
}

wss.on("connection", async (socket) => {
  console.log("Dashboard connected.");

  // loop demo transactions every 12s so you can watch it repeatedly
  let running = true;
  socket.on("close", () => {
    running = false;
    console.log("Dashboard disconnected.");
  });

  while (running) {
    await runDemoTransaction(socket);
    await delay(4000);
  }
});