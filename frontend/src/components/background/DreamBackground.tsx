import type { ReactNode } from "react";
import { SoftGlowLayer } from "./SoftGlowLayer";
import { StaticStarLayer } from "./StaticStarLayer";

type DreamBackgroundProps = {
  variant: "main" | "chatbot" | "detail";
  children: ReactNode;
};

export function DreamBackground({ variant, children }: DreamBackgroundProps) {
  return (
    <div className={`dream-background dream-background--${variant}`}>
      <SoftGlowLayer />
      <StaticStarLayer />
      <div className="dream-background__content">{children}</div>
    </div>
  );
}
