"use client";

import { MarkdownRenderer } from "@/components/markdown/markdown-renderer";
import { cn } from "@/lib/utils";
import type { MinorityReport } from "@/types/chat";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronRight, Scale } from "lucide-react";
import { useState } from "react";

interface MinorityReportPanelProps {
  reports: MinorityReport[];
  isDeadlock?: boolean;
  agreementScore?: number;
  primaryDisagreement?: string;
}

function ReportCard({ report }: { report: MinorityReport }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg bg-surface/80 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer hover:bg-surface-overlay/40 transition-colors"
      >
        <ChevronRight
          className={cn(
            "w-4 h-4 text-muted shrink-0 transition-transform",
            expanded && "rotate-90"
          )}
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">{report.model}</p>
          {report.role && (
            <p className="text-xs text-muted mt-0.5">{report.role}</p>
          )}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4 border-t border-border-subtle/60">
              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted mb-2">
                  Minority Opinion
                </p>
                <p className="text-xs text-muted">
                  This model reached a substantively different conclusion from the majority.
                </p>
              </div>

              {report.reasoning && (
                <div>
                  <p className="text-[11px] uppercase tracking-wider text-muted mb-2">
                    Reasoning
                  </p>
                  <div className="rounded-md bg-surface-overlay/50 px-3 py-2.5">
                    <MarkdownRenderer
                      content={report.reasoning}
                      className="text-sm opacity-90"
                    />
                  </div>
                </div>
              )}

              <div>
                <p className="text-[11px] uppercase tracking-wider text-muted mb-2">
                  Response
                </p>
                <MarkdownRenderer content={report.response} className="text-sm" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function MinorityReportPanel({
  reports,
  isDeadlock,
  agreementScore,
  primaryDisagreement,
}: MinorityReportPanelProps) {
  const [expanded, setExpanded] = useState(isDeadlock ?? false);

  if (reports.length === 0) return null;

  return (
    <div
      className={cn(
        "mt-6 rounded-xl overflow-hidden",
        isDeadlock
          ? "ring-1 ring-[var(--accent-warm)]/30 bg-[var(--accent-warm)]/[0.04]"
          : "ring-1 ring-border-subtle bg-surface-overlay/30"
      )}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-3 w-full px-5 py-4 text-left cursor-pointer hover:bg-surface-overlay/30 transition-colors"
      >
        <Scale
          className={cn(
            "w-4 h-4 shrink-0",
            isDeadlock ? "text-[var(--accent-warm)]" : "text-accent"
          )}
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">
            {isDeadlock ? "View Minority Report" : "Minority Perspectives"}
          </p>
          {isDeadlock && agreementScore !== undefined && (
            <p className="text-xs text-muted mt-0.5">
              Agreement: {(agreementScore * 100).toFixed(0)}%
              {primaryDisagreement && (
                <span className="hidden sm:inline"> · {primaryDisagreement}</span>
              )}
            </p>
          )}
        </div>
        <ChevronRight
          className={cn(
            "w-4 h-4 text-muted shrink-0 transition-transform",
            expanded && "rotate-90"
          )}
        />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-3 border-t border-border-subtle/60">
              {isDeadlock && primaryDisagreement && (
                <div className="pt-4 pb-1">
                  <p className="text-[11px] uppercase tracking-wider text-muted mb-1">
                    Primary Disagreement
                  </p>
                  <p className="text-sm">{primaryDisagreement}</p>
                </div>
              )}
              {reports.map((report) => (
                <ReportCard key={report.modelId} report={report} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
