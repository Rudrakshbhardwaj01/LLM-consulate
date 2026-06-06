export function SeoContent() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-3xl mx-auto prose-consulate text-muted text-sm leading-relaxed space-y-8">
        <article>
          <h2
            className="text-2xl text-foreground font-normal mb-3"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            What is multi-model AI?
          </h2>
          <p>
            Multi-model AI sends a single prompt to several language models
            simultaneously. Instead of relying on one perspective, you receive
            independent analyses from models with different architectures and
            training. LLM Consulate orchestrates these requests concurrently and
            presents both individual responses and a unified answer.
          </p>
        </article>

        <article>
          <h2
            className="text-2xl text-foreground font-normal mb-3"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            What is consensus generation?
          </h2>
          <p>
            Consensus generation is the process of synthesizing multiple model
            responses into one authoritative answer. After each model responds
            independently, a synthesis engine identifies agreement, resolves
            disagreements, and produces a final response that reflects the
            strongest reasoning across all participants. This reduces
            single-model bias and surfaces nuance when models diverge.
          </p>
        </article>

        <article>
          <h2
            className="text-2xl text-foreground font-normal mb-3"
            style={{ fontFamily: "var(--font-display-family)" }}
          >
            How LLM Consulate works
          </h2>
          <p>
            LLM Consulate offers two modes. In Direct Chat, you converse with a
            single open-source model through NVIDIA Inference APIs. In Consulate
            Mode, you select multiple models, submit one prompt, and watch each
            model respond in parallel. A synthesis step then generates the
            consensus answer. All orchestration runs on a dedicated FastAPI
            backend with async streaming — no third-party AI frameworks.
          </p>
        </article>
      </div>
    </section>
  );
}
