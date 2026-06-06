"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export function CTA() {
  return (
    <section className="py-24 px-6">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-2xl mx-auto text-center"
      >
        <h2
          className="text-3xl sm:text-4xl font-normal mb-4"
          style={{ fontFamily: "var(--font-display-family)" }}
        >
          Ready to consult the council?
        </h2>
        <p className="text-muted mb-8 max-w-md mx-auto">
          No sign-up. No API keys required for local models. Just open the
          consulate and start asking.
        </p>
        <Button asChild size="lg" className="gap-2 text-base px-8">
          <Link href="/chat">
            Start Consulting
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </motion.div>
    </section>
  );
}
