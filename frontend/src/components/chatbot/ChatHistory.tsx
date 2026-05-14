import { memo } from "react";
import type { ChatTurn } from "../../types";

interface Props {
  history: ChatTurn[];
  isLoading?: boolean;
}

export const ChatHistory = memo(function ChatHistory({ history, isLoading }: Props) {
  if (history.length === 0) {
    return <p className="chat-empty">무엇이든 물어보세요. DJ가 답해드릴게요.</p>;
  }

  return (
    <div className="chat-history">
      {history.map((turn, idx) => {
        const isLast = idx === history.length - 1;
        const showLoading = isLast && isLoading && !turn.chatbot_response;
        return (
          <div key={idx} className="chat-turn">
            {turn.user_input && (
              <div className="chat-bubble chat-bubble--user">{turn.user_input}</div>
            )}
            {turn.chatbot_response && (
              <div className="chat-bubble chat-bubble--bot">{turn.chatbot_response}</div>
            )}
            {showLoading && (
              <div className="chat-bubble chat-bubble--bot chat-bubble--loading">
                <span className="loading-dot" />
                <span className="loading-dot" />
                <span className="loading-dot" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
});
