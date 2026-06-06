"use client";

import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { motion } from "framer-motion";
import { MessageSquare, Users } from "lucide-react";

const SUGGESTED_PROMPTS = {
  direct: [
    "Explain a concept I'm struggling with",
    "Help me draft a technical document",
    "Review this approach and suggest improvements",
  ],
  consulate: [
    "Should I prioritize depth or breadth in my career?",
    "Compare two architectural approaches for my project",
    "What are the trade-offs I should consider?",
  ],
};

interface EmptyStateProps {
  onSend?: (content: string) => void;
}

export function EmptyState({ onSend }: EmptyStateProps) {
  const mode = useChatStore((s) => s.mode);
  const isGenerating = useChatStore((s) => s.isGenerating);
  const prompts = SUGGESTED_PROMPTS[mode];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center text-center px-6 py-24 max-w-lg mx-auto"
    >
      <div className="w-14 h-14 rounded-2xl bg-accent/8 flex items-center justify-center mb-8">
        {mode === "consulate" ? (
          <Users className="w-6 h-6 text-accent" />
        ) : (
          <MessageSquare className="w-6 h-6 text-accent" />
        )}
      </div>

      <h2
        className="text-2xl sm:text-3xl font-normal mb-4"
        style={{ fontFamily: "var(--font-display-family)" }}
      >
        {mode === "consulate" ? "Consult the Council" : "Start a Conversation"}
      </h2>

      <p className="text-muted leading-relaxed text-sm mb-8 max-w-sm">
        {mode === "consulate" ? (
          <>
            Multiple frontier models will reason independently about your
            question, evaluate agreement, and synthesize a response — or
            document where they disagree.
          </>
        ) : (
          <>
            Select a model above and ask anything. Switch to Consulate Mode
            when you want multiple perspectives.
          </>
        )}
      </p>

      <div className="w-full space-y-2">
        <p className="text-[11px] uppercase tracking-wider text-muted/60 mb-3">
          Try asking
        </p>
        {prompts.map((prompt, i) => (
          <motion.button
            key={prompt}
            type="button"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.05 }}
            disabled={!onSend || isGenerating}
            onClick={() => onSend?.(prompt)}
            className={cn(
              "w-full text-sm text-muted/80 px-4 py-3 rounded-xl",
              "bg-surface-overlay/40 ring-1 ring-border-subtle/50",
              "transition-colors text-left",
              onSend &&
                "hover:bg-surface-overlay/70 hover:text-foreground cursor-pointer",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            &ldquo;{prompt}&rdquo;
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
