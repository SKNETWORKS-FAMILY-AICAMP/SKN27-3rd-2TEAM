import { memo } from "react";
import type { KeyboardEvent } from "react";
import { DreamButton } from "../ui/DreamButton";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}

export const ChatInput = memo(function ChatInput({ value, onChange, onSend, disabled }: Props) {
  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-input">
      <textarea
        className="chat-input__textarea"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKey}
        placeholder="음악에 대해 물어보세요..."
        disabled={disabled}
        rows={2}
      />
      <DreamButton
        className="chat-input__send"
        onClick={onSend}
        disabled={disabled || !value.trim()}
      >
        {disabled ? "..." : "전송"}
      </DreamButton>
    </div>
  );
});
