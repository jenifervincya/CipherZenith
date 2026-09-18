// StepFlow.jsx
import StepCard from "./StepCard";

const STEP_DEFINITIONS = [
  { step: 1, title: "Transaction Received" },
  { step: 2, title: "Hybrid Encryption" },
  { step: 3, title: "AI Monitoring" },
  { step: 4, title: "Threat Detection" },
  { step: 5, title: "Adaptive Engine" },
  { step: 6, title: "Self Healing" },
  { step: 7, title: "Multi-path Transmission" },
  { step: 8, title: "Secure Output" },
];

/**
 * stepStates: { [stepNumber]: { status, details, timestamp } }
 * populated live as WebSocket messages arrive — see Dashboard.jsx
 */
export default function StepFlow({ stepStates }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
      {STEP_DEFINITIONS.map(({ step, title }) => {
        const state = stepStates[step] ?? { status: "idle", details: {} };
        return (
          <StepCard
            key={step}
            index={step}
            title={title}
            status={state.status}
            details={state.details}
            timestamp={state.timestamp}
          />
        );
      })}
    </div>
  );
}