import { memo, useState, useEffect } from "react";
import { motion } from "framer-motion";

export type MascotState = "idle" | "thinking" | "talking" | "recommending" | "fallback";

interface Props {
  state?: MascotState;
}

const BASE = "/mascot/";

function useMascotImages() {
  const [hasImages, setHasImages] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.onload = () => setHasImages(true);
    img.onerror = () => setHasImages(false);
    img.src = `${BASE}body.png`;
  }, []);

  return hasImages;
}

function useBlinkTimer() {
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    let handle: ReturnType<typeof setTimeout>;

    const schedule = () => {
      const delay = 4000 + Math.random() * 3000;
      handle = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          schedule();
        }, 180);
      }, delay);
    };

    schedule();
    return () => clearTimeout(handle);
  }, []);

  return isBlinking;
}

const FLOAT_ANIMATE = {
  idle:        { y: [0, -12, 0] },
  thinking:    { rotate: [-3, 3, -3] },
  talking:     { y: [0, -6, 0] },
  recommending:{ y: [0, -8, 0], scale: [1, 1.03, 1] },
  fallback:    { y: [0, -4, 0] },
};

const FLOAT_TRANSITION: Record<MascotState, { duration: number; repeat: number; ease: "easeInOut" }> = {
  idle:         { duration: 4,   repeat: Infinity, ease: "easeInOut" },
  thinking:     { duration: 2,   repeat: Infinity, ease: "easeInOut" },
  talking:      { duration: 1.5, repeat: Infinity, ease: "easeInOut" },
  recommending: { duration: 2,   repeat: Infinity, ease: "easeInOut" },
  fallback:     { duration: 5,   repeat: Infinity, ease: "easeInOut" },
};

const GLOW_OPACITY: Record<MascotState, number[]> = {
  idle: [0.3, 0.6, 0.3],
  thinking: [0.2, 0.4, 0.2],
  talking: [0.4, 0.7, 0.4],
  recommending: [0.55, 1, 0.55],
  fallback: [0.15, 0.3, 0.15],
};

const GLOW_DURATION: Record<MascotState, number> = {
  idle: 3,
  thinking: 2,
  talking: 1.5,
  recommending: 2,
  fallback: 4,
};

export const MascotCharacter = memo(function MascotCharacter({ state = "idle" }: Props) {
  const hasImages = useMascotImages();
  const isBlinking = useBlinkTimer();

  const eyeSrc = isBlinking ? `${BASE}eyes_closed.png` : `${BASE}eyes_open.png`;

  return (
    <div className="mascot-wrap">
      <motion.div
        className="mascot-glow"
        animate={{ opacity: GLOW_OPACITY[state] }}
        transition={{ duration: GLOW_DURATION[state], repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div className="mascot-float" animate={FLOAT_ANIMATE[state]} transition={FLOAT_TRANSITION[state]}>
        <div className="mascot-body">
          {hasImages ? (
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
                  <img src={`${BASE}music_note_01.png`} alt="" className="mascot-layer" style={{ animation: "note-float 2s ease-out infinite" }} />
                  <img src={`${BASE}music_note_02.png`} alt="" className="mascot-layer" style={{ animation: "note-float 2s ease-out infinite 0.8s" }} />
                </>
              )}
            </>
          ) : (
            <div className="mascot-placeholder">🎧</div>
          )}
        </div>
      </motion.div>
    </div>
  );
});
