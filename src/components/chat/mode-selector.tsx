"use client";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { motion } from "framer-motion";
import { MessageSquare, Users } from "lucide-react";

export function ModeSelector() {
  const { mode, setMode, isGenerating } = useChatStore();

  return (
    <div className="flex items-center gap-1 p-1 rounded-lg bg-surface-overlay border border-border">
      <button
        onClick={() => setMode("direct")}
        disabled={isGenerating}
        className={cn(
          "relative flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer disabled:opacity-50",
          mode === "direct"
            ? "text-foreground"
            : "text-muted hover:text-foreground"
        )}
      >
        {mode === "direct" && (
          <motion.div
            layoutId="mode-indicator"
            className="absolute inset-0 bg-surface rounded-md shadow-sm border border-border"
            transition={{ type: "spring", duration: 0.4, bounce: 0.15 }}
          />
        )}
        <MessageSquare className="w-3.5 h-3.5 relative z-10" />
        <span className="relative z-10">Direct</span>
      </button>

      <button
        onClick={() => setMode("consulate")}
        disabled={isGenerating}
        className={cn(
          "relative flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer disabled:opacity-50",
          mode === "consulate"
            ? "text-foreground"
            : "text-muted hover:text-foreground"
        )}
      >
        {mode === "consulate" && (
          <motion.div
            layoutId="mode-indicator"
            className="absolute inset-0 bg-surface rounded-md shadow-sm border border-border"
            transition={{ type: "spring", duration: 0.4, bounce: 0.15 }}
          />
        )}
        <Users className="w-3.5 h-3.5 relative z-10" />
        <span className="relative z-10">Consulate</span>
      </button>
    </div>
  );
}
