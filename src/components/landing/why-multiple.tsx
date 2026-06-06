"use client";

import { motion } from "framer-motion";

const reasons = [
  {
    title: "Reduced single-model bias",
    description:
      "One model can be confidently wrong. Multiple models cross-check each other's reasoning.",
  },
  {
    title: "Broader knowledge coverage",
    description:
      "Different models excel at different domains. Together, they cover more ground.",
  },
  {
    title: "Higher confidence answers",
    description:
      "When models agree, you can trust the answer. When they disagree, you see the nuance.",
  },
  {
    title: "Transparent reasoning",
    description:
      "Expand any consulate response to see exactly what each model said. Nothing hidden.",
  },
];

export function WhyMultiple() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2
            className="text-3xl sm:text-4xl font-normal mb-4"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            Why ask multiple models?
          </h2>
          <p className="text-muted max-w-lg">
            A single answer is a single perspective. Important questions deserve
            more than one point of view.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 gap-8">
          {reasons.map((reason, i) => (
            <motion.div
              key={reason.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
            >
              <h3 className="text-base font-medium mb-2 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0" />
                {reason.title}
              </h3>
              <p className="text-sm text-muted leading-relaxed pl-3.5">
                {reason.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
