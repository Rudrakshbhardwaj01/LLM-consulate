"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const faqs = [
  {
    q: "Why not just use a single model?",
    a: "A single model gives you one perspective, trained on one set of biases. When the stakes are high — career decisions, technical architecture, research synthesis — you want independent reasoning from multiple models. Disagreement between them is often more valuable than false agreement from one.",
  },
  {
    q: "How does Consulate Mode work?",
    a: "Your prompt goes to each selected model in parallel. Each model responds independently, without seeing the others. Once responses arrive, we measure how much they agree, identify dissenting views, and synthesize a final answer that reflects the council's collective judgment — or documents where they couldn't reach consensus.",
  },
  {
    q: "What happens when models disagree?",
    a: "Disagreement is expected and useful. When agreement falls below the threshold, the council is declared deadlocked. You'll see the agreement score, the primary point of contention, and expandable minority reports showing exactly which models dissented and why. The final summary presents both sides rather than forcing a false consensus.",
  },
  {
    q: "Does consensus mean the answer is correct?",
    a: "No. Consensus means multiple independent models reached similar conclusions — which increases confidence, but doesn't guarantee correctness. Models can all be wrong in the same direction. When they disagree, that's a signal to think harder, not a failure of the system.",
  },
  {
    q: "Why can different models reach different conclusions?",
    a: "Each model has different training data, architecture, and reasoning patterns. One may prioritize practical constraints while another emphasizes theoretical completeness. These differences are features, not bugs — they surface assumptions you might otherwise miss.",
  },
  {
    q: "Which model generates the final answer?",
    a: "A dedicated synthesis model (GPT-OSS 120B by default) reads all council responses and produces the final answer. It doesn't simply pick one response — it weighs the arguments, identifies common ground, and notes where views diverge. You can inspect every individual response separately.",
  },
  {
    q: "Can I inspect individual model responses?",
    a: "Yes. After any Consulate response completes, expand \"Inspect individual model responses\" to see exactly what each model said, including reasoning traces where available. Nothing is hidden behind the synthesis.",
  },
  {
    q: "Why are some responses slower than others?",
    a: "Models vary in size, reasoning depth, and current API load. Reasoning models often take longer because they work through problems step by step. All models run in parallel, so total wait time is determined by the slowest responder, not the sum of all requests.",
  },
  {
    q: "How is my data handled?",
    a: "Conversations stay in your browser — nothing is stored on our servers. When you send a prompt, it goes directly to the model provider API (NVIDIA) for inference. No accounts, no tracking, no cloud storage of your messages.",
  },
  {
    q: "Can I trust the consensus more than a single model?",
    a: "When models agree, you have stronger evidence that the answer holds up under different reasoning approaches. When they disagree, you have early warning that the question may not have a straightforward answer. Either outcome is more informative than a single confident response.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="py-28 px-6">
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-14"
        >
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted/70 mb-3">
            Common questions
          </p>
          <h2
            className="text-3xl sm:text-4xl font-normal"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            What you might be wondering
          </h2>
        </motion.div>

        <div className="divide-y divide-border-subtle">
          {faqs.map((faq, i) => (
            <motion.div
              key={faq.q}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.03 }}
            >
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                aria-expanded={openIndex === i}
                className="w-full flex items-start justify-between gap-4 py-5 text-left cursor-pointer group"
              >
                <span className="text-sm font-medium pr-4 group-hover:text-accent transition-colors">
                  {faq.q}
                </span>
                <ChevronDown
                  className={cn(
                    "w-4 h-4 text-muted shrink-0 mt-0.5 transition-transform",
                    openIndex === i && "rotate-180"
                  )}
                />
              </button>
              <AnimatePresence initial={false}>
                {openIndex === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <p className="text-sm text-muted leading-relaxed pb-5 pr-8">
                      {faq.a}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
