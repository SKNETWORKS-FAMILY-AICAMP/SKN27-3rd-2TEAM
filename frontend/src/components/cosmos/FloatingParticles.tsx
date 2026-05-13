import { memo, type CSSProperties } from "react";

const particles = [
  { id: "p1", x: 12, y: 24, delay: 0, duration: 9 },
  { id: "p2", x: 28, y: 68, delay: 1.8, duration: 11 },
  { id: "p3", x: 45, y: 18, delay: 0.7, duration: 10 },
  { id: "p4", x: 63, y: 74, delay: 2.2, duration: 12 },
  { id: "p5", x: 82, y: 30, delay: 1.1, duration: 10 },
  { id: "p6", x: 90, y: 62, delay: 3, duration: 13 },
];

export const FloatingParticles = memo(function FloatingParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden" aria-hidden="true">
      {particles.map((particle) => (
        <span
          key={particle.id}
          className="absolute h-1 w-1 rounded-full bg-[#ffe8be]/60 blur-[0.2px] animate-[cosmic-dust-float_var(--duration)_ease-in-out_infinite]"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            animationDelay: `${particle.delay}s`,
            "--duration": `${particle.duration}s`,
          } as CSSProperties}
        />
      ))}
    </div>
  );
});
