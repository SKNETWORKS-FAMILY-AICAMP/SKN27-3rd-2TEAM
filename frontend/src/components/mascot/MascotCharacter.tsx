import { memo, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  mascotIdle,
  mascotRecommending,
  mascotTalking,
  mascotThinking,
} from "../../styles/motion";

export type MascotState = "idle" | "thinking" | "talking" | "recommending" | "fallback";

interface Props {
  state?: MascotState;
}

const BASE = "/mascot/";
const SINGLE_IMAGE = `${BASE}mascot.png`;

function useMascotImages() {
  const [imageMode, setImageMode] = useState<"single" | "layered" | "fallback">("fallback");

  useEffect(() => {
    const single = new Image();
    single.onload = () => setImageMode("single");
    single.onerror = () => {
      const body = new Image();
      body.onload = () => setImageMode("layered");
      body.onerror = () => setImageMode("fallback");
      body.src = `${BASE}body.png`;
    };
    single.src = SINGLE_IMAGE;
  }, []);

  return imageMode;
}

function useBlinkTimer() {
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    let handle: ReturnType<typeof setTimeout>;
    let blinkHandle: ReturnType<typeof setTimeout>;

    const schedule = () => {
      const delay = 4000 + Math.random() * 3000;
      handle = setTimeout(() => {
        setIsBlinking(true);
        blinkHandle = setTimeout(() => {
          setIsBlinking(false);
          schedule();
        }, 180);
      }, delay);
    };

    schedule();
    return () => {
      clearTimeout(handle);
      clearTimeout(blinkHandle);
    };
  }, []);

  return isBlinking;
}

const MOTION_PRESET = {
  idle: mascotIdle,
  thinking: mascotThinking,
  talking: mascotTalking,
  recommending: mascotRecommending,
  fallback: mascotIdle,
};

const GLOW_OPACITY: Record<MascotState, number[]> = {
  idle: [0.3, 0.55, 0.3],
  thinking: [0.25, 0.42, 0.25],
  talking: [0.34, 0.58, 0.34],
  recommending: [0.42, 0.7, 0.42],
  fallback: [0.18, 0.3, 0.18],
};

const GLOW_DURATION: Record<MascotState, number> = {
  idle: 3.4,
  thinking: 3,
  talking: 2.6,
  recommending: 3.4,
  fallback: 4,
};

export const MascotCharacter = memo(function MascotCharacter({ state = "idle" }: Props) {
  const imageMode = useMascotImages();
  const isBlinking = useBlinkTimer();
  const preset = MOTION_PRESET[state];
  const eyeSrc = isBlinking ? `${BASE}eyes_closed.png` : `${BASE}eyes_open.png`;

  return (
    <div className="mascot-wrap">
      <motion.div
        className="mascot-glow"
        animate={{ opacity: GLOW_OPACITY[state] }}
        transition={{ duration: GLOW_DURATION[state], repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div className="mascot-float" animate={preset.animate} transition={preset.transition}>
        <div className="mascot-body">
          {imageMode === "single" ? (
            <img src={SINGLE_IMAGE} alt="뮤엘 mascot" className="mascot-image" />
          ) : imageMode === "layered" ? (
            <>
              <img src={`${BASE}body.png`} alt="" className="mascot-layer" />
              <img src={`${BASE}head.png`} alt="" className="mascot-layer" />
              <img src={eyeSrc} alt="" className="mascot-layer" />
              <img src={`${BASE}headphone.png`} alt="" className="mascot-layer" />
              {state === "talking" && (
                <img src={`${BASE}mouth_talk_01.png`} alt="" className="mascot-layer" />
              )}
              {state === "recommending" && (
                <>
                  <img src={`${BASE}music_note_01.png`} alt="" className="mascot-layer" />
                  <img src={`${BASE}music_note_02.png`} alt="" className="mascot-layer" />
                </>
              )}
            </>
          ) : (
            <div className="mascot-placeholder">뮤엘</div>
          )}
        </div>
      </motion.div>
    </div>
  );
});
