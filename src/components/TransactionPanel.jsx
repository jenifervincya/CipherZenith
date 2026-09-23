// TransactionPanel.jsx
import { sanitizeDisplayText } from "../../security/csp_headers";

/**
 * transaction: { id, sender, receiver, amount, timestamp } | null
 */
export default function TransactionPanel({ transaction }) {
  if (!transaction) {
    return (
      <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5">
        <p className="text-xs font-mono text-white/30">
          Waiting for a transaction from CipherPay…
        </p>
      </div>
    );
  }

  const { id, sender, receiver, amount, timestamp } = transaction;

  return (
    <div className="rounded-md bg-[#0b0f14] border border-white/5 p-5 space-y-4">
      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">TRANSACTION ID</p>
        <p className="font-mono text-sm text-cyan-400">{sanitizeDisplayText(id)}</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1">
          <p className="text-[10px] font-mono tracking-wider text-white/30">SENDER</p>
          <p className="text-sm text-white/90">{sanitizeDisplayText(sender)}</p>
        </div>
        <span className="text-white/20 text-lg">&rarr;</span>
        <div className="flex-1">
          <p className="text-[10px] font-mono tracking-wider text-white/30">RECEIVER</p>
          <p className="text-sm text-white/90">{sanitizeDisplayText(receiver)}</p>
        </div>
      </div>

      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">AMOUNT</p>
        <p className="font-mono text-lg text-white/90">
          &#8377;{Number(amount).toLocaleString("en-IN")}
        </p>
      </div>

      <div>
        <p className="text-[10px] font-mono tracking-wider text-white/30">TIMESTAMP</p>
        <p className="font-mono text-xs text-white/50">{sanitizeDisplayText(timestamp)}</p>
      </div>
    </div>
  );
}