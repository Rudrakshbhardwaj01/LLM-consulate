import { Logo } from "@/components/brand/logo";

export function Footer() {
  return (
    <footer className="border-t border-border py-8 px-6">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted">
        <Logo size={24} className="text-foreground" />
        <p>Open-source models only. Built with intention.</p>
        <p>&copy; {new Date().getFullYear()}</p>
      </div>
    </footer>
  );
}
