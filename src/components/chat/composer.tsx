"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { ArrowUp } from "lucide-react";
import { useCallback, useRef, useState } from "react";

interface ComposerProps {
  onSend: (content: string) => void;
}

export function Composer({ onSend }: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { isGenerating } = useChatStore();
  const isExhausted = useSessionStore((s) => s.isExhausted());

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }, []);

  const handleSend = () => {
    if (!value.trim() || isGenerating || isExhausted) return;
    onSend(value);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-surface/80 backdrop-blur-sm p-4">
      <div className="max-w-3xl mx-auto">
        <div
          className={cn(
            "relative flex items-end gap-2 rounded-xl border border-border bg-surface p-2 shadow-sm transition-colors",
            "focus-within:border-accent/40 focus-within:shadow-md"
          )}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              adjustHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              isExhausted
                ? "Session limit reached"
                : "Ask the consulate…"
            }
            disabled={isGenerating || isExhausted}
            rows={1}
            className="flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-relaxed placeholder:text-muted focus:outline-none disabled:opacity-50 max-h-[200px] scrollbar-thin"
          />
          <Button
            size="icon"
            className="h-9 w-9 shrink-0 rounded-lg"
            onClick={handleSend}
            disabled={!value.trim() || isGenerating || isExhausted}
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-[11px] text-muted/60 text-center mt-2">
          {typeof navigator !== "undefined" && navigator.platform?.includes("Mac")
            ? "⌘"
            : "Ctrl"}
          +Enter to send
        </p>
      </div>
    </div>
  );
}
