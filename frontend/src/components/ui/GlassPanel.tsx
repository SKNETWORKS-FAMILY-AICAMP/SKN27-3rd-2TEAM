import type { ReactNode } from "react";

export type GlassPanelProps = {
  children: ReactNode;
  className?: string;
  intensity?: "base" | "strong";
};

export function GlassPanel({ children, className = "", intensity = "base" }: GlassPanelProps) {
  const classes = ["glass-panel", `glass-panel--${intensity}`, className]
    .filter(Boolean)
    .join(" ");

  return <div className={classes}>{children}</div>;
}
