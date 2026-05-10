import { memo } from "react";

interface Props {
  userId: string;
}

export const ChatbotHeader = memo(function ChatbotHeader({ userId }: Props) {
  return (
    <header className="chatbot-header">
      <span className="chatbot-header__icon">🎵</span>
      <span className="chatbot-header__title">RIMAS DJ</span>
      <span className="chatbot-header__user">{userId}</span>
    </header>
  );
});
