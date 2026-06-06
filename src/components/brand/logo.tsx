import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: number;
  showWordmark?: boolean;
}

export function Logo({ className, size = 32, showWordmark = true }: LogoProps) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="shrink-0"
      >
        <circle
          cx="20"
          cy="20"
          r="18"
          stroke="currentColor"
          strokeWidth="1"
          className="text-border opacity-60"
        />
        <path
          d="M20 6 A18 18 0 0 1 35.6 28"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="text-accent"
        />
        <path
          d="M35.6 28 A18 18 0 0 1 4.4 28"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="text-accent opacity-70"
        />
        <path
          d="M4.4 28 A18 18 0 0 1 20 6"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="text-accent opacity-50"
        />
        <circle cx="20" cy="20" r="3" fill="currentColor" className="text-accent" />
      </svg>
      {showWordmark && (
        <span
          className="text-lg tracking-tight"
          style={{ fontFamily: "var(--font-display-family)" }}
        >
          LLM Consulate
        </span>
      )}
    </span>
  );
}
