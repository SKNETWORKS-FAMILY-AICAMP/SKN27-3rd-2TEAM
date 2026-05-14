import { memo } from "react";

interface Props {
  userId: string;
  onHomeClick?: () => void;
}

export const ChatbotHeader = memo(function ChatbotHeader({ userId, onHomeClick }: Props) {
  return (
    <header className="chatbot-header">
      <span className="chatbot-header__icon">🎵</span>
      <span className="chatbot-header__title">RIMAS DJ</span>
      <span className="chatbot-header__user">{userId}</span>
      {onHomeClick && (
        <button className="chatbot-header__home-btn" type="button" onClick={onHomeClick}>
          홈
        </button>
      )}
    </header>
  );
});
