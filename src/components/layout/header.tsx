"use client";

import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";
import Link from "next/link";

export function Header() {
  return (
    <TooltipProvider>
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <Link href="/" className="hover:text-accent transition-colors">
            <Logo size={28} />
          </Link>

          <nav className="hidden sm:flex items-center gap-6 text-sm text-muted">
            <a href="#how-it-works" className="hover:text-foreground transition-colors">
              How It Works
            </a>
            <a href="#faq" className="hover:text-foreground transition-colors">
              FAQ
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button asChild size="sm">
              <Link href="/chat">Open Chat</Link>
            </Button>
          </div>
        </div>
      </header>
    </TooltipProvider>
  );
}
