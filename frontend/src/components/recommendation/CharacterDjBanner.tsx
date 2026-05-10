import { memo } from "react";
import { MascotCharacter } from "../mascot/MascotCharacter";

interface Props {
  message: string;
  onChatOpen?: () => void;
}

export const CharacterDjBanner = memo(function CharacterDjBanner({ message, onChatOpen }: Props) {
  return (
    <div className="dj-hero">
      <div className="dj-hero__mascot">
        <MascotCharacter state="idle" />
      </div>

      <div className="dj-hero__content">
        <span className="dj-hero__label">Tonight's Curator</span>
        <p className="dj-hero__message">
          {message || "오늘 밤의 음악 흐름을\n함께 탐색해봐요."}
        </p>
        <p className="dj-hero__sub">
          당신의 취향 너머, 새로운 음악과 만나는 공간
        </p>
        {onChatOpen && (
          <button className="dj-hero__cta" onClick={onChatOpen}>
            DJ와 이야기하기 →
          </button>
        )}
      </div>
    </div>
  );
});
