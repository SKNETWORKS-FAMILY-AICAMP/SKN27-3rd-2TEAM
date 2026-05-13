import { memo } from "react";

type Props = {
  className?: string;
};

export const GlowRing = memo(function GlowRing({ className = "" }: Props) {
  return (
    <span
      className={[
        "pointer-events-none absolute inset-0 rounded-full border border-white/10",
        "shadow-[0_0_42px_rgba(255,214,185,0.16),inset_0_0_48px_rgba(255,255,255,0.05)]",
        "before:absolute before:inset-[10%] before:rounded-full before:border before:border-white/5",
        "after:absolute after:inset-[-8%] after:rounded-full after:bg-[radial-gradient(circle,rgba(255,214,185,0.16),transparent_66%)] after:blur-md",
        className,
      ].join(" ")}
      aria-hidden="true"
    />
  );
});
