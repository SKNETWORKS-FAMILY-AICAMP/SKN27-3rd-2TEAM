import { memo } from "react";
import { motion } from "framer-motion";
import { MascotCharacter } from "../mascot/MascotCharacter";
import { GlowRing } from "./GlowRing";

type Props = {
  layout?: "desktop" | "mobile";
};

export const CenterMascotOrb = memo(function CenterMascotOrb({ layout = "desktop" }: Props) {
  const positionClassName =
    layout === "desktop"
      ? "absolute left-1/2 top-[48%] -translate-x-1/2 -translate-y-1/2"
      : "relative";

  return (
    <motion.div
      className={`${positionClassName} z-[6] flex flex-col items-center`}
      animate={{ y: [0, -7, 0], scale: [1, 1.012, 1] }}
      transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
    >
      <div className="relative grid h-[17rem] w-[17rem] place-items-center rounded-full border border-white/10 bg-white/[0.045] shadow-[0_0_58px_rgba(255,211,184,0.18),inset_0_0_60px_rgba(255,255,255,0.045)] backdrop-blur-xl md:h-[20rem] md:w-[20rem]">
        <GlowRing />
        <div className="relative z-[1] h-[12.2rem] w-[12.2rem] md:h-[14.2rem] md:w-[14.2rem]">
          <MascotCharacter state="idle" />
        </div>
        <span className="absolute bottom-7 z-[2] text-[0.95rem] font-black tracking-[0.34em] text-[#fff2dc]/90 drop-shadow-[0_2px_14px_rgba(0,0,0,0.45)] md:bottom-8 md:text-[1.05rem]">
          RIMAS
        </span>
      </div>
    </motion.div>
  );
});
