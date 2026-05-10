import { memo } from "react";
import type { ChatTurn } from "../../types";

interface Props {
  history: ChatTurn[];
}

export const ChatHistory = memo(function ChatHistory({ history }: Props) {
  if (history.length === 0) {
    return <p className="chat-empty">무엇이든 물어보세요. DJ가 답해드릴게요 🎵</p>;
  }

  return (
    <div className="chat-history">
      {history.map((turn, idx) => (
        <div key={idx} className="chat-turn">
          <div className="chat-bubble chat-bubble--user">{turn.user_input}</div>
          <div className="chat-bubble chat-bubble--bot">{turn.chatbot_response}</div>
        </div>
      ))}
    </div>
  );
});
