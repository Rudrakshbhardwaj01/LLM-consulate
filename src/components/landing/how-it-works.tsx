"use client";

import { motion } from "framer-motion";

const steps = [
  {
    number: "01",
    title: "Your Prompt",
    description: "Ask any question. The same prompt goes to every selected model.",
  },
  {
    number: "02",
    title: "Independent Reasoning",
    description:
      "Each model analyzes your question separately, drawing on its own training and perspective.",
  },
  {
    number: "03",
    title: "Individual Responses",
    description:
      "You see each model's answer in real time. Progress indicators show who's responded.",
  },
  {
    number: "04",
    title: "Consensus Answer",
    description:
      "A synthesis engine reviews all responses and produces a unified, authoritative answer.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6 bg-surface/50">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2
            className="text-3xl sm:text-4xl font-normal mb-4"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            How Consulate Mode works
          </h2>
          <p className="text-muted max-w-lg mx-auto">
            Four steps from question to consensus.
          </p>
        </motion.div>

        <div className="space-y-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, x: -16 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="flex gap-6 items-start"
            >
              <span
                className="text-3xl font-light text-accent/40 shrink-0 w-12"
                style={{ fontFamily: "var(--font-display-family)" }}
              >
                {step.number}
              </span>
              <div>
                <h3 className="text-lg font-medium mb-1">{step.title}</h3>
                <p className="text-sm text-muted leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
