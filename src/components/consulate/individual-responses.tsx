"use client";

import { MarkdownRenderer } from "@/components/markdown/markdown-renderer";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";
import type { ConsulateMessageData } from "@/types/chat";
import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronRight, Clock, X } from "lucide-react";

interface IndividualResponsesProps {
  messageId: string;
  data: ConsulateMessageData;
}

export function IndividualResponses({
  messageId,
  data,
}: IndividualResponsesProps) {
  const { expandedConsulatePanels, toggleConsulatePanel } = useUIStore();
  const isExpanded = expandedConsulatePanels.has(messageId);

  const responses = data.individualResponses.filter(
    (r) =>
      r.status === "complete" ||
      r.status === "error" ||
      r.status === "timeout"
  );

  if (responses.length === 0) return null;

  const completedCount = responses.filter(
    (r) => r.status === "complete" && r.content
  ).length;

  return (
    <div className="mt-6 pt-5 border-t border-border-subtle/60">
      <button
        onClick={() => toggleConsulatePanel(messageId)}
        className="flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors cursor-pointer group w-full text-left"
      >
        <ChevronRight
          className={cn(
            "w-4 h-4 transition-transform shrink-0",
            isExpanded && "rotate-90"
          )}
        />
        <span>
          Inspect individual model responses
          <span className="ml-1.5 text-xs opacity-60">
            ({completedCount} of {responses.length})
          </span>
        </span>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3">
              {responses.map((resp) => (
                <div
                  key={resp.modelId}
                  className="rounded-xl bg-surface-overlay/40 p-4 ring-1 ring-border-subtle/50"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div>
                      <span className="text-sm font-medium">
                        {resp.modelName || resp.modelId}
                      </span>
                      {resp.role && (
                        <span className="text-xs text-muted ml-2">
                          {resp.role}
                        </span>
                      )}
                    </div>
                    {resp.status === "complete" ? (
                      <Check className="w-3.5 h-3.5 text-green-500 shrink-0" />
                    ) : resp.status === "timeout" ? (
                      <Clock className="w-3.5 h-3.5 text-[var(--accent-warm)] shrink-0" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-muted shrink-0" />
                    )}
                  </div>

                  {resp.error ? (
                    <p className="text-sm text-muted">{resp.error}</p>
                  ) : resp.status === "timeout" ? (
                    <p className="text-sm text-[var(--accent-warm)]">
                      Response timed out before completing.
                    </p>
                  ) : (
                    <>
                      {resp.reasoning && (
                        <div className="mb-3 pb-3 border-b border-border-subtle/50">
                          <p className="text-[11px] uppercase tracking-wider text-muted mb-2">
                            Reasoning
                          </p>
                          <MarkdownRenderer
                            content={resp.reasoning}
                            className="text-sm opacity-85"
                          />
                        </div>
                      )}
                      <MarkdownRenderer
                        content={resp.content}
                        className="text-sm"
                      />
                    </>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
