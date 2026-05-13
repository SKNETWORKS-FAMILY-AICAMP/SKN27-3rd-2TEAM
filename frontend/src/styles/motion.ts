import type { Variants } from "framer-motion";

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: "easeOut" },
  },
};

export const softFloat = {
  animate: { y: [0, -8, 0] },
  transition: { duration: 4, repeat: Infinity, ease: "easeInOut" as const },
};

export const cardHover = {
  y: -2,
  scale: 1.01,
  transition: { duration: 0.2, ease: "easeOut" as const },
};

export const mascotIdle = {
  animate: { y: [0, -8, 0] },
  transition: { duration: 4.2, repeat: Infinity, ease: "easeInOut" as const },
};

export const mascotThinking = {
  animate: { y: [0, -5, 0] },
  transition: { duration: 3.2, repeat: Infinity, ease: "easeInOut" as const },
};

export const mascotTalking = {
  animate: { y: [0, -4, 0] },
  transition: { duration: 2.6, repeat: Infinity, ease: "easeInOut" as const },
};

export const mascotRecommending = {
  animate: { y: [0, -7, 0], scale: [1, 1.01, 1] },
  transition: { duration: 3.4, repeat: Infinity, ease: "easeInOut" as const },
};
