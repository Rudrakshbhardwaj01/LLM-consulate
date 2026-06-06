"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center px-6 overflow-hidden">
      <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
      </div>

      <div className="relative max-w-3xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-sm uppercase tracking-[0.2em] text-muted mb-6">
            Multi-Model AI Platform
          </p>

          <h1
            className="text-5xl sm:text-6xl md:text-7xl font-normal leading-[1.1] mb-8"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            One Prompt.
            <br />
            <span className="text-accent">Multiple Minds.</span>
          </h1>

          <div className="text-lg sm:text-xl text-muted leading-relaxed max-w-xl mx-auto mb-10 space-y-4">
            <p>
              Most AI products give you one answer.
            </p>
            <p>
              LLM Consulate gathers multiple frontier models, compares their
              reasoning, identifies disagreement, and presents a synthesized
              response.
            </p>
            <p className="text-foreground/80 italic">
              Consult a council instead of a single machine.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button asChild size="lg" className="gap-2 text-base px-8">
              <Link href="/chat">
                Enter the Consulate
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="text-base px-8">
              <a href="#how-it-works">See How It Works</a>
            </Button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mt-20 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs text-muted/60 uppercase tracking-wider"
        >
          <span>Open Source Only</span>
          <span className="hidden sm:block w-px h-3 bg-border" />
          <span>No Sign-Up Required</span>
          <span className="hidden sm:block w-px h-3 bg-border" />
          <span>15 Free Requests</span>
        </motion.div>
      </div>
    </section>
  );
}
