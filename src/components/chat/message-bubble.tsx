"use client";

import { MarkdownRenderer } from "@/components/markdown/markdown-renderer";
import { ConsulateProgress } from "@/components/consulate/consulate-progress";
import { IndividualResponses } from "@/components/consulate/individual-responses";
import { MinorityReportPanel } from "@/components/consulate/minority-report";
import { cn } from "@/lib/utils";
import type { Message } from "@/types/chat";
import { motion } from "framer-motion";
import { AlertCircle, AlertTriangle, User } from "lucide-react";
import { MessageActions } from "./message-actions";

interface MessageBubbleProps {
  message: Message;
  onRegenerate?: () => void;
}

export function MessageBubble({ message, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const data = message.consulateData;
  const isDeadlock = data?.isDeadlock ?? data?.consensusOutcome === "deadlock";
  const outcomeLabel =
    data?.outcomeLabel ??
    (isDeadlock ? "Council Deadlocked" : "Consensus Reached");

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "group flex gap-4 px-4 sm:px-6 py-6",
        isUser ? "bg-transparent" : "bg-surface/30"
      )}
    >
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-medium",
          isUser
            ? "bg-accent/10 text-accent"
            : "bg-surface-overlay text-muted"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <svg width="16" height="16" viewBox="0 0 40 40" fill="none" aria-hidden>
            <circle cx="20" cy="20" r="3" fill="currentColor" className="text-accent" />
            <path
              d="M20 6 A18 18 0 0 1 35.6 28"
              stroke="currentColor"
              strokeWidth="2"
              fill="none"
              className="text-accent"
            />
          </svg>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span className="text-xs font-medium text-muted">
            {isUser ? "You" : message.mode === "consulate" ? "Consulate" : "Assistant"}
          </span>

          {message.mode === "consulate" && !isUser && !message.isStreaming && (
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full",
                isDeadlock
                  ? "bg-[var(--accent-warm)]/10 text-[var(--accent-warm)]"
                  : "bg-accent/10 text-accent"
              )}
            >
              {isDeadlock ? "Deadlock Summary" : outcomeLabel}
            </span>
          )}

          {message.consulateData?.synthesisDegraded && !message.isStreaming && (
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400">
              Synthesis unavailable — showing council summary
            </span>
          )}

          {message.consulateData?.councilTotal &&
            message.consulateData.councilResponded !== undefined &&
            !message.isStreaming &&
            message.consulateData.councilResponded <
              message.consulateData.councilTotal && (
              <span className="text-[10px] text-muted">
                {message.consulateData.councilResponded} of{" "}
                {message.consulateData.councilTotal} council members responded
              </span>
            )}
        </div>

        {message.error && (
          <div
            role="alert"
            className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400 mb-3 p-3 rounded-lg bg-red-500/5 ring-1 ring-red-500/20"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{message.error}</span>
          </div>
        )}

        {message.consulateData && message.isStreaming && (
          <ConsulateProgress
            data={message.consulateData}
            isStreaming={message.isStreaming}
          />
        )}

        {!isDeadlock &&
          !message.isStreaming &&
          data?.agreementScore !== undefined &&
          message.content && (
            <div className="mb-5 rounded-xl p-4 ring-1 ring-accent/20 bg-accent/[0.04]">
              <p className="text-sm font-medium text-accent">{outcomeLabel}</p>
              <p className="text-xs text-muted mt-1">
                Vote Support:{" "}
                {((data.majoritySupport ?? 0) * 100).toFixed(0)}%
                {" · "}
                Agreement Score: {(data.agreementScore * 100).toFixed(0)}%
                {data.confidenceLevel && (
                  <span> · Confidence: {data.confidenceLevel}</span>
                )}
              </p>
              {data.disagreement && (data.minoritySupport ?? 0) > 0 && (
                <div className="mt-3 space-y-2 text-sm">
                  <p>
                    <span className="text-muted">Reason for disagreement: </span>
                    {data.disagreement.disputedConcept}
                  </p>
                  {data.supportingModels && data.supportingModels.length > 0 && (
                    <p className="text-xs text-muted">
                      Supporting: {data.supportingModels.join(", ")}
                    </p>
                  )}
                  {data.minorityModels && data.minorityModels.length > 0 && (
                    <p className="text-xs text-muted">
                      Minority ({((data.minoritySupport ?? 0) * 100).toFixed(0)}%):{" "}
                      {data.disagreement.minorityPosition}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

        {isDeadlock &&
          !message.isStreaming &&
          message.content &&
          data?.agreementScore !== undefined && (
            <div className="mb-5 rounded-xl p-4 ring-1 ring-[var(--accent-warm)]/25 bg-[var(--accent-warm)]/[0.04]">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-[var(--accent-warm)] shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-[var(--accent-warm)]">
                    Council Deadlocked
                  </p>
                  <p className="text-xs text-muted mt-1">
                    Vote Support: {((data.majoritySupport ?? 0) * 100).toFixed(0)}%
                    {" · "}
                    Agreement Score: {(data.agreementScore * 100).toFixed(0)}%
                  </p>
                  {data.primaryDisagreement && (
                    <p className="text-sm mt-2">
                      <span className="text-muted">Primary disagreement: </span>
                      {data.primaryDisagreement}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

        {message.content ? (
          <div className="min-h-[1.5rem]">
            <MarkdownRenderer content={message.content} />
          </div>
        ) : message.isStreaming ? (
          <div className="flex items-center gap-2 text-sm text-muted py-1 min-h-[1.5rem]">
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse-subtle" />
              <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse-subtle [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-muted animate-pulse-subtle [animation-delay:0.4s]" />
            </span>
          </div>
        ) : null}

        {!isUser && (
          <MessageActions
            content={message.content}
            onRegenerate={onRegenerate}
            isStreaming={message.isStreaming}
          />
        )}

        {message.consulateData?.minorityReports &&
          message.consulateData.minorityReports.length > 0 &&
          !message.isStreaming && (
            <MinorityReportPanel
              reports={message.consulateData.minorityReports}
              isDeadlock={message.consulateData.isDeadlock}
              agreementScore={message.consulateData.agreementScore}
              primaryDisagreement={message.consulateData.primaryDisagreement}
            />
          )}

        {message.consulateData && !message.isStreaming && message.content && (
          <IndividualResponses
            messageId={message.id}
            data={message.consulateData}
          />
        )}
      </div>
    </motion.div>
  );
}
