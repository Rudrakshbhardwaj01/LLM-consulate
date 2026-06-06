"use client";

import { cn } from "@/lib/utils";
import type { ConsulateMessageData, ConsulateStage } from "@/types/chat";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Circle,
  Clock,
  Loader2,
  X,
} from "lucide-react";

const STAGE_FLOW: { stage: ConsulateStage; label: string }[] = [
  { stage: "initializing", label: "Council Assembling" },
  { stage: "receiving", label: "Receiving Responses" },
  { stage: "analyzing", label: "Evaluating Agreement" },
  { stage: "synthesizing", label: "Generating Consensus" },
  { stage: "complete", label: "Final Answer Ready" },
];

const DEADLOCK_FLOW: { stage: ConsulateStage; label: string }[] = [
  { stage: "initializing", label: "Council Assembling" },
  { stage: "receiving", label: "Receiving Responses" },
  { stage: "analyzing", label: "Evaluating Agreement" },
  { stage: "deadlock", label: "Council Deadlocked" },
];

function stageIndex(stage: ConsulateStage, isDeadlock: boolean): number {
  const flow = isDeadlock ? DEADLOCK_FLOW : STAGE_FLOW;
  const idx = flow.findIndex((s) => s.stage === stage);
  return idx >= 0 ? idx : 0;
}

function StatusDot({
  status,
  supportsReasoning,
}: {
  status: string;
  supportsReasoning?: boolean;
}) {
  switch (status) {
    case "complete":
      return (
        <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
          <Check className="w-3 h-3" />
          <span>Complete</span>
        </span>
      );
    case "streaming":
      return (
        <span className="flex items-center gap-1.5 text-accent">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-accent opacity-40 animate-ping" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
          <span>{supportsReasoning ? "Thinking" : "Responding"}</span>
        </span>
      );
    case "error":
      return (
        <span className="flex items-center gap-1.5 text-muted">
          <X className="w-3 h-3" />
          <span>Unavailable</span>
        </span>
      );
    case "timeout":
      return (
        <span className="flex items-center gap-1.5 text-[var(--accent-warm)]">
          <Clock className="w-3 h-3" />
          <span>Timed out</span>
        </span>
      );
    default:
      return (
        <span className="flex items-center gap-1.5 text-muted/50">
          <Circle className="w-2 h-2" />
          <span>Waiting</span>
        </span>
      );
  }
}

interface ConsulateProgressProps {
  data: ConsulateMessageData;
  isStreaming: boolean;
}

export function ConsulateProgress({ data, isStreaming }: ConsulateProgressProps) {
  const stage = data.currentStage ?? "initializing";
  const isDeadlock = data.isDeadlock || stage === "deadlock";
  const flow = isDeadlock ? DEADLOCK_FLOW : STAGE_FLOW;
  const currentIdx = stageIndex(stage, isDeadlock);

  if (!isStreaming && (stage === "complete" || stage === "deadlock")) {
    return null;
  }

  const councilNote =
    data.councilTotal &&
    data.councilResponded !== undefined &&
    data.councilResponded < data.councilTotal
      ? `${data.councilResponded} of ${data.councilTotal} council members responded`
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl p-5 mb-5",
        isDeadlock
          ? "bg-[var(--accent-warm)]/[0.06] ring-1 ring-[var(--accent-warm)]/25"
          : "bg-surface-overlay/40 ring-1 ring-border-subtle"
      )}
    >
      <div className="mb-5">
        <p className="text-[11px] uppercase tracking-[0.15em] text-muted/70 mb-3">
          Prompt submitted
        </p>
        <div className="space-y-2">
          {flow.map((step, i) => {
            const isPast = i < currentIdx;
            const isCurrent = i === currentIdx;
            const isFuture = i > currentIdx;

            return (
              <motion.div
                key={step.stage}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className={cn(
                  "flex items-center gap-3 text-sm",
                  isFuture && "opacity-30",
                  isPast && "text-muted",
                  isCurrent && "text-foreground font-medium"
                )}
              >
                <span
                  className={cn(
                    "w-1.5 h-1.5 rounded-full shrink-0 transition-colors",
                    isPast && "bg-accent/60",
                    isCurrent && !isDeadlock && "bg-accent animate-pulse-subtle",
                    isCurrent &&
                      isDeadlock &&
                      step.stage === "deadlock" &&
                      "bg-[var(--accent-warm)]",
                    isFuture && "bg-border"
                  )}
                />
                <span>{step.label}</span>
                {isCurrent && isStreaming && step.stage !== "complete" && (
                  <Loader2 className="w-3.5 h-3.5 text-muted animate-spin ml-auto" />
                )}
                {isPast && <Check className="w-3.5 h-3.5 text-accent/60 ml-auto" />}
              </motion.div>
            );
          })}
        </div>
      </div>

      <AnimatePresence>
        {isDeadlock && data.agreementScore !== undefined && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 pb-4 border-b border-[var(--accent-warm)]/20"
          >
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-[var(--accent-warm)] shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-[var(--accent-warm)]">
                  Council Deadlocked
                </p>
                <p className="text-xs text-muted mt-0.5">
                  Vote Support: {((data.majoritySupport ?? 0) * 100).toFixed(0)}%
                  {" · "}
                  Agreement Score: {(data.agreementScore * 100).toFixed(0)}%
                </p>
                {data.primaryDisagreement && (
                  <p className="text-xs mt-2">
                    <span className="text-muted">Primary disagreement: </span>
                    <span className="text-foreground">
                      {data.primaryDisagreement}
                    </span>
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isDeadlock &&
        data.majoritySupport !== undefined &&
        (stage === "analyzing" || stage === "synthesizing") && (
          <p className="text-xs text-muted mb-4">
            {data.outcomeLabel ?? "Consensus"} · Vote support:{" "}
            {(data.majoritySupport * 100).toFixed(0)}%
            {data.agreementScore !== undefined && (
              <span> · Agreement: {(data.agreementScore * 100).toFixed(0)}%</span>
            )}
          </p>
        )}

      {(stage === "receiving" ||
        stage === "analyzing" ||
        stage === "synthesizing" ||
        stage === "deadlock") &&
        data.individualResponses.length > 0 && (
          <div className="space-y-2">
            {data.individualResponses.map((resp, i) => (
              <motion.div
                key={resp.modelId}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center justify-between gap-3 py-1.5"
              >
                <span
                  className={cn(
                    "text-sm truncate",
                    resp.status === "complete" ? "text-foreground" : "text-muted"
                  )}
                >
                  {resp.modelName || resp.modelId}
                </span>
                <span className="text-xs shrink-0">
                  <StatusDot
                    status={resp.status}
                    supportsReasoning={resp.supportsReasoning}
                  />
                </span>
              </motion.div>
            ))}
          </div>
        )}

      {councilNote && (
        <p className="text-xs text-muted mt-4 pt-3 border-t border-border-subtle">
          {councilNote}
        </p>
      )}

      {isDeadlock && isStreaming && stage === "deadlock" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 flex items-center gap-2 text-xs text-muted"
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>Documenting dissent and preparing summary…</span>
        </motion.div>
      )}
    </motion.div>
  );
}
