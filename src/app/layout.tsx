import { ThemeProvider } from "@/components/providers/theme-provider";
import type { Metadata } from "next";
import {
  Fraunces,
  Instrument_Serif,
  JetBrains_Mono,
  Source_Serif_4,
} from "next/font/google";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-instrument",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-body-family",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-family",
  display: "swap",
});

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "LLM Consulate — One Prompt. Multiple Minds.",
    template: "%s | LLM Consulate",
  },
  description:
    "Consult multiple open-source language models through a single interface. Where AI models confer before they answer. Multi-model consensus generation powered by NVIDIA.",
  keywords: [
    "multi-model AI",
    "LLM consensus",
    "open source AI",
    "NVIDIA inference",
    "AI orchestration",
    "Consulate Mode",
  ],
  authors: [{ name: "LLM Consulate" }],
  creator: "LLM Consulate",
  openGraph: {
    title: "LLM Consulate — One Prompt. Multiple Minds.",
    description:
      "Consult multiple language models. Independent reasoning. Synthesized consensus.",
    type: "website",
    url: BASE_URL,
    siteName: "LLM Consulate",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "LLM Consulate",
    description: "One Prompt. Multiple Minds.",
  },
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: BASE_URL,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${instrumentSerif.variable} ${fraunces.variable} ${sourceSerif.variable} ${jetbrainsMono.variable} font-body antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange={false}
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
