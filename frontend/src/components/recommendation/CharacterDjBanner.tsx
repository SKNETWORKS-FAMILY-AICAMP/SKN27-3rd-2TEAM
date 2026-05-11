import { memo } from "react";
import { MascotCharacter } from "../mascot/MascotCharacter";
import type { MascotState } from "../mascot/MascotCharacter";
import { DreamButton } from "../ui/DreamButton";
import { GlassPanel } from "../ui/GlassPanel";

interface Props {
  message: string;
  onChatOpen?: () => void;
  mascotState?: MascotState;
}

export const CharacterDjBanner = memo(function CharacterDjBanner({
  message,
  onChatOpen,
  mascotState = "idle",
}: Props) {
  return (
    <GlassPanel className="dj-hero" intensity="strong">
      <div className="dj-hero__decorations" aria-hidden="true">
        <span className="dj-hero__float dj-hero__float--note">♪</span>
        <span className="dj-hero__float dj-hero__float--star">✦</span>
        <span className="dj-hero__float dj-hero__float--dot" />
        <span className="dj-hero__float dj-hero__float--small-note">♫</span>
        <span className="dj-hero__float dj-hero__float--small-dot" />
      </div>

      <div className="dj-hero__mascot">
        <MascotCharacter state={mascotState} />
      </div>

      <div className="dj-hero__content">
        <span className="dj-hero__label">
          <span aria-hidden="true">✦</span>
          Tonight's Curator
        </span>
        <p className="dj-hero__message">
          {message || "오늘 밤의 음악 흐름을 함께 살펴볼게요."}
        </p>
        <p className="dj-hero__sub">
          API가 전달한 추천 결과를 몽환적인 카드로 정리했습니다.
        </p>
        {onChatOpen && (
          <DreamButton className="dj-hero__cta" onClick={onChatOpen}>
            DJ와 이야기하기
          </DreamButton>
        )}
      </div>
    </GlassPanel>
  );
});
