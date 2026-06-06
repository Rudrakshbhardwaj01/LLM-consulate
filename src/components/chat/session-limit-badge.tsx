"use client";

import { cn } from "@/lib/utils";
import { getRemainingRequests } from "@/lib/session/limits";
import { useSessionStore } from "@/stores/session-store";
import { motion } from "framer-motion";

export function SessionLimitBadge({ className }: { className?: string }) {
  const requestsUsed = useSessionStore((s) => s.requestsUsed);
  const remaining = getRemainingRequests(requestsUsed);
  const isLow = remaining <= 5;

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "text-xs font-medium tracking-wide px-3 py-1.5 rounded-full border",
        isLow
          ? "border-[var(--accent-warm)] text-[var(--accent-warm)] bg-[var(--accent-warm)]/5"
          : "border-border text-muted bg-surface-overlay",
        className
      )}
    >
      {remaining} {remaining === 1 ? "Request" : "Requests"} Remaining
    </motion.div>
  );
}
