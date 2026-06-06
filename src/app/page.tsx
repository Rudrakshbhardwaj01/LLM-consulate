import { CTA } from "@/components/landing/cta";
import { FAQ } from "@/components/landing/faq";
import { Features } from "@/components/landing/features";
import { Hero } from "@/components/landing/hero";
import { HowItWorks } from "@/components/landing/how-it-works";
import { JsonLd } from "@/components/landing/json-ld";
import { SeoContent } from "@/components/landing/seo-content";
import { WhyMultiple } from "@/components/landing/why-multiple";
import { Footer } from "@/components/layout/footer";
import { Header } from "@/components/layout/header";

export default function LandingPage() {
  return (
    <>
      <JsonLd />
      <Header />
      <main className="pt-16">
        <Hero />
        <Features />
        <HowItWorks />
        <WhyMultiple />
        <SeoContent />
        <div id="faq">
          <FAQ />
        </div>
        <CTA />
      </main>
      <Footer />
    </>
  );
}
