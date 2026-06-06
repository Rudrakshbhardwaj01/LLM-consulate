"use client";

import { useChatStore } from "@/stores/chat-store";
import { useUIStore } from "@/stores/ui-store";
import { useEffect } from "react";

export function useKeyboardShortcuts() {
  const { createConversation, setMode, mode } = useChatStore();
  const { toggleSidebar } = useUIStore();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const meta = e.metaKey || e.ctrlKey;

      if (meta && e.key === "n") {
        e.preventDefault();
        createConversation();
      }

      if (meta && e.shiftKey && e.key === "C") {
        e.preventDefault();
        setMode(mode === "direct" ? "consulate" : "direct");
      }

      if (meta && e.key === "b") {
        e.preventDefault();
        toggleSidebar();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [createConversation, setMode, mode, toggleSidebar]);
}
