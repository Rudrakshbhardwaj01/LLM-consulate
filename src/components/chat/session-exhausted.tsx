"use client";

import { Button } from "@/components/ui/button";
import { useSessionStore } from "@/stores/session-store";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import Link from "next/link";

export function SessionExhausted() {
  const reset = useSessionStore((s) => s.reset);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center text-center px-6 py-16 max-w-md mx-auto"
    >
      <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-6">
        <Sparkles className="w-7 h-7 text-accent" />
      </div>

      <h2
        className="text-2xl font-medium mb-3"
        style={{ fontFamily: "var(--font-display-family)" }}
      >
        Your session has reached its limit
      </h2>

      <p className="text-muted leading-relaxed mb-8">
        You&apos;ve used all 15 guest requests in this session. LLM Consulate
        is designed to give you a taste of multi-model intelligence — create an
        account in a future release for unlimited access.
      </p>

      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          variant="secondary"
          onClick={() => {
            reset();
            window.location.reload();
          }}
        >
          Start Fresh Session
        </Button>
        <Button asChild>
          <Link href="/">Learn More</Link>
        </Button>
      </div>
    </motion.div>
  );
}
