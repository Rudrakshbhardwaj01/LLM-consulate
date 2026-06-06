"use client";

import { useChat } from "@/hooks/use-chat";
import { useStickToBottom } from "@/hooks/use-stick-to-bottom";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { isSessionExhausted } from "@/lib/session/limits";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";
import { useMemo } from "react";
import { Composer } from "./composer";
import { EmptyState } from "./empty-state";
import { MessageBubble } from "./message-bubble";
import { ModeSelector } from "./mode-selector";
import { ModelPicker } from "./model-picker";
import { SessionExhausted } from "./session-exhausted";
import { Sidebar } from "./sidebar";
import { SessionLimitBadge } from "./session-limit-badge";
import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";
import Link from "next/link";

export function ChatShell() {
  const { sendMessage, regenerate } = useChat();
  const conversation = useChatStore((s) =>
    s.conversations.find((c) => c.id === s.activeConversationId) ?? null
  );
  const requestsUsed = useSessionStore((s) => s.requestsUsed);
  const isExhausted = isSessionExhausted(requestsUsed);
  const messages = useMemo(
    () => conversation?.messages ?? [],
    [conversation?.messages]
  );
  const isStreaming = messages.some((m) => m.isStreaming);
  const { containerRef, onScroll } = useStickToBottom(messages, isStreaming);

  useKeyboardShortcuts();

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />

        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex items-center justify-between px-4 sm:px-6 py-3 bg-surface/60 backdrop-blur-md shrink-0 border-b border-border-subtle">
            <div className="flex items-center gap-3">
              <Link href="/" className="hover:opacity-80 transition-opacity">
                <Logo size={24} />
              </Link>
              <div className="hidden sm:block w-px h-4 bg-border" />
              <div className="hidden sm:flex items-center gap-2">
                <ModeSelector />
                <ModelPicker />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <SessionLimitBadge />
              <ThemeToggle />
            </div>
          </header>

          <div className="sm:hidden flex items-center gap-2 px-4 py-2 border-b border-border-subtle">
            <ModeSelector />
            <ModelPicker />
          </div>

          <div
            ref={containerRef}
            onScroll={onScroll}
            className="flex-1 overflow-y-auto scrollbar-thin overscroll-contain"
          >
            {isExhausted && messages.length === 0 ? (
              <SessionExhausted />
            ) : messages.length === 0 ? (
              <EmptyState onSend={sendMessage} />
            ) : (
              <div className="max-w-3xl mx-auto">
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    onRegenerate={
                      msg.role === "assistant"
                        ? () => regenerate(msg.id)
                        : undefined
                    }
                  />
                ))}
              </div>
            )}
          </div>

          <Composer onSend={sendMessage} />
        </div>
      </div>
    </TooltipProvider>
  );
}
