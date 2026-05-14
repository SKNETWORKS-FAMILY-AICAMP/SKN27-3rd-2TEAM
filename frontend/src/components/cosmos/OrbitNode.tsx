import { memo } from "react";
import { motion } from "framer-motion";
import { GlowRing } from "./GlowRing";

export type OrbitFeature = {
  id: string;
  title: string;
  position: "left-top" | "right-top" | "left-bottom" | "right-bottom";
  imageSrc: string;
  target: "personalized" | "discovery" | "newRelease" | "chatbot";
  x: number;
  y: number;
  controlX: number;
  controlY: number;
};

type Props = {
  feature: OrbitFeature;
  onSelect: (target: OrbitFeature["target"]) => void;
};

const positionClassName: Record<OrbitFeature["position"], string> = {
  "left-top": "left-[22%] top-[28%]",
  "right-top": "left-[78%] top-[30%]",
  "left-bottom": "left-[23%] top-[70%]",
  "right-bottom": "left-[76%] top-[68%]",
};

export const OrbitNode = memo(function OrbitNode({ feature, onSelect }: Props) {
  return (
    <motion.button
      type="button"
      className={[
        "group absolute z-[7] flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-3 text-[#fff2dc]",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-8 focus-visible:outline-[#ffe5bd]/80",
        "max-md:static max-md:translate-x-0 max-md:translate-y-0",
        positionClassName[feature.position],
      ].join(" ")}
      whileHover={{ y: -4, scale: 1.025 }}
      whileTap={{ scale: 0.985 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      onClick={() => onSelect(feature.target)}
      aria-label={`${feature.title} 화면으로 이동`}
    >
      <span className="relative grid h-[8rem] w-[8rem] place-items-center rounded-full border border-[#ffe6bf]/20 bg-white/[0.07] shadow-[0_0_42px_rgba(255,220,180,0.28),inset_0_0_34px_rgba(255,255,255,0.06)] backdrop-blur-xl transition-[border-color,box-shadow] duration-300 group-hover:border-[#ffe6bf]/55 group-hover:shadow-[0_0_64px_rgba(255,224,184,0.48),inset_0_0_48px_rgba(255,255,255,0.09)] md:h-[8.9rem] md:w-[8.9rem]">
        <GlowRing className="opacity-90 transition-opacity duration-300 group-hover:opacity-100" />
        <img className="relative z-[1] h-[68%] w-[68%] object-contain brightness-110 drop-shadow-[0_0_18px_rgba(255,230,180,0.55)] transition-[filter] duration-300 group-hover:brightness-125 group-hover:drop-shadow-[0_0_26px_rgba(255,230,180,0.80)]" src={feature.imageSrc} alt="" aria-hidden="true" />
      </span>
      <span className="text-[1rem] font-extrabold tracking-[0.01em] text-[#fff1dd]/90 drop-shadow-[0_2px_12px_rgba(0,0,0,0.55)] md:text-[1.14rem]">
        {feature.title}
      </span>
    </motion.button>
  );
});
