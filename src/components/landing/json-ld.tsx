const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export function JsonLd() {
  const softwareApp = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "LLM Consulate",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description:
      "Multi-model AI platform that consults multiple language models and generates consensus answers.",
    url: BASE_URL,
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };

  const faqPage = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "What is Consulate Mode?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Consulate Mode sends your prompt to multiple models simultaneously. Each responds independently, then a synthesis engine produces a consensus answer.",
        },
      },
      {
        "@type": "Question",
        name: "Which models does LLM Consulate use?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "LLM Consulate uses open-source models via NVIDIA Inference APIs, including Llama, Gemma, Mistral, Phi, and Nemotron.",
        },
      },
      {
        "@type": "Question",
        name: "Is an account required?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "No. LLM Consulate offers a guest experience with 15 requests per session. Conversations are stored locally in your browser.",
        },
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareApp) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqPage) }}
      />
    </>
  );
}
