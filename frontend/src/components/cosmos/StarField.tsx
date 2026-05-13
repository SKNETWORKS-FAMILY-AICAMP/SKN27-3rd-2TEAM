import { memo } from "react";

type Star = {
  id: string;
  x: number;
  y: number;
  size: number;
  opacity: number;
  delay: number;
  sparkle?: boolean;
};

const stars: Star[] = [
  { id: "s1", x: 8, y: 12, size: 1, opacity: 0.72, delay: 0.1 },
  { id: "s2", x: 18, y: 7, size: 1.5, opacity: 0.82, delay: 1.2, sparkle: true },
  { id: "s3", x: 32, y: 17, size: 1, opacity: 0.58, delay: 0.5 },
  { id: "s4", x: 47, y: 9, size: 1.25, opacity: 0.72, delay: 1.6 },
  { id: "s5", x: 62, y: 14, size: 1, opacity: 0.5, delay: 2.1 },
  { id: "s6", x: 78, y: 8, size: 1.8, opacity: 0.88, delay: 0.3, sparkle: true },
  { id: "s7", x: 91, y: 15, size: 1, opacity: 0.62, delay: 1.4 },
  { id: "s8", x: 12, y: 36, size: 1.2, opacity: 0.76, delay: 2.4 },
  { id: "s9", x: 39, y: 33, size: 1, opacity: 0.5, delay: 0.9 },
  { id: "s10", x: 56, y: 29, size: 1.4, opacity: 0.78, delay: 1.8, sparkle: true },
  { id: "s11", x: 84, y: 41, size: 1, opacity: 0.6, delay: 0.7 },
  { id: "s12", x: 6, y: 61, size: 1, opacity: 0.56, delay: 2.2 },
  { id: "s13", x: 21, y: 57, size: 1.5, opacity: 0.84, delay: 0.4, sparkle: true },
  { id: "s14", x: 69, y: 58, size: 1, opacity: 0.55, delay: 1.1 },
  { id: "s15", x: 93, y: 66, size: 1.2, opacity: 0.66, delay: 2.6 },
  { id: "s16", x: 15, y: 82, size: 1, opacity: 0.54, delay: 1.5 },
  { id: "s17", x: 44, y: 78, size: 1.3, opacity: 0.74, delay: 0.2 },
  { id: "s18", x: 60, y: 86, size: 1, opacity: 0.58, delay: 1.9 },
  { id: "s19", x: 81, y: 80, size: 1.6, opacity: 0.82, delay: 0.8, sparkle: true },
  { id: "s20", x: 96, y: 90, size: 1, opacity: 0.48, delay: 2.8 },
];

export const StarField = memo(function StarField() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[1]" aria-hidden="true">
      {stars.map((star) => (
        <span
          key={star.id}
          className={[
            "absolute rounded-full bg-[#fff3cf] shadow-[0_0_8px_rgba(255,229,178,0.62)]",
            "animate-[cosmic-twinkle_4.8s_ease-in-out_infinite]",
            star.sparkle ? "cosmic-star-sparkle" : "",
          ].join(" ")}
          style={{
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: `${star.size * 2}px`,
            height: `${star.size * 2}px`,
            opacity: star.opacity,
            animationDelay: `${star.delay}s`,
          }}
        />
      ))}
    </div>
  );
});
