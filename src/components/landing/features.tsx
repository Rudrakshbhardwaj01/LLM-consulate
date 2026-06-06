"use client";

import { motion } from "framer-motion";
import { Brain, GitMerge, History, Shield } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Direct Chat",
    description:
      "Talk to any frontier model individually — GPT-OSS, Qwen, Gemma, Kimi, Nemotron, and MiniMax via NVIDIA Inference APIs.",
  },
  {
    icon: GitMerge,
    title: "Consulate Mode",
    description:
      "Send one prompt to multiple models. Each responds independently. Agreement is measured, dissent is surfaced, and a synthesis engine produces the final answer.",
  },
  {
    icon: History,
    title: "Local History",
    description:
      "Conversations persist in your browser. Create, rename, and manage multiple threads. No account needed.",
  },
  {
    icon: Shield,
    title: "Open Source Only",
    description:
      "Every model in the registry is open source. Served through NVIDIA's inference platform with a centralized, extensible model registry.",
  },
];

export function Features() {
  return (
    <section className="py-28 px-6">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16"
        >
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted/70 mb-3">
            Capabilities
          </p>
          <h2
            className="text-3xl sm:text-4xl font-normal mb-4"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            Built for thoughtful inquiry
          </h2>
          <p className="text-muted max-w-lg">
            Not another chatbot wrapper. A deliberate interface for consulting
            multiple perspectives.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 gap-x-12 gap-y-10">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="group"
            >
              <div className="w-9 h-9 rounded-lg bg-accent/8 flex items-center justify-center mb-4 group-hover:bg-accent/12 transition-colors">
                <feature.icon className="w-4 h-4 text-accent" />
              </div>
              <h3 className="text-base font-medium mb-2">{feature.title}</h3>
              <p className="text-sm text-muted leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
