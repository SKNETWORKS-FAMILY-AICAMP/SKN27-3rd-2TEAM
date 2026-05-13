import { memo } from "react";

export type ConstellationPoint = {
  id: string;
  x: number;
  y: number;
  controlX: number;
  controlY: number;
};

type Props = {
  points: ConstellationPoint[];
};

export const ConstellationLines = memo(function ConstellationLines({ points }: Props) {
  return (
    <svg className="pointer-events-none absolute inset-0 z-[4] h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <filter id="soft-line-glow">
          <feGaussianBlur stdDeviation="0.45" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {points.map((point) => (
        <g key={point.id}>
          <path
            d={`M 50 50 Q ${point.controlX} ${point.controlY} ${point.x} ${point.y}`}
            fill="none"
            stroke="rgba(255,226,185,0.52)"
            strokeDasharray="0.8 1.7"
            strokeLinecap="round"
            strokeWidth="0.18"
            filter="url(#soft-line-glow)"
          />
          <circle cx={point.x} cy={point.y} r="0.48" fill="rgba(255,236,199,0.78)" filter="url(#soft-line-glow)" />
          <circle cx={(point.x + 50) / 2} cy={(point.y + 50) / 2} r="0.34" fill="rgba(255,236,199,0.54)" />
        </g>
      ))}
    </svg>
  );
});
