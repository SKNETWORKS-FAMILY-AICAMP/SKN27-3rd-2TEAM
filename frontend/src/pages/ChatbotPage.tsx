/**
 * 챗봇 페이지.
 *
 * API 호출, 세션 히스토리 로드, response_state 처리 흐름은 기존 계약을 유지한다.
 */
import { useQuery } from "@tanstack/react-query";
import { useState, useCallback, useEffect, useRef } from "react";
import { fetchSessionHistory, flushSession, sendChatMessageStream } from "../api/chatbot";
import { addToTaste } from "../api/taste";
import { DreamBackground } from "../components/background/DreamBackground";
import { ChatHistory } from "../components/chatbot/ChatHistory";
import { ChatInput } from "../components/chatbot/ChatInput";
import { ChatbotHeader } from "../components/chatbot/ChatbotHeader";
import { RelatedRecommendationCards } from "../components/chatbot/RelatedRecommendationCards";
import { GlassPanel } from "../components/ui/GlassPanel";
import { useChatStore } from "../stores/chatStore";
import { useSessionStore } from "../stores/sessionStore";
import { generateRequestId } from "../utils/requestId";

interface Props {
  onNavigateHome?: () => void;
}

export function ChatbotPage({ onNavigateHome }: Props) {
  const { userId, sessionId, resetSession } = useSessionStore();
  const {
    history, isLoading,
    appendUserTurn,
    appendAssistantDelta, finalizeAssistantTurn, replaceLastAssistantMessage,
    setHistory, setLoading, clear,
  } = useChatStore();
  const [input, setInput] = useState("");
  const [showExitModal, setShowExitModal] = useState(false);
  const [exitLoading, setExitLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const streamingRef = useRef(false);

  const { data: historyData } = useQuery({
    queryKey: ["session-history", sessionId],
    queryFn: () => fetchSessionHistory(sessionId, userId),
    staleTime: Infinity,
    retry: false,
  });

  useEffect(() => {
    if (historyData?.history) {
      setHistory(historyData.history);
    }
  }, [historyData, setHistory]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || streamingRef.current) return;
    setInput("");
    setLoading(true);
    streamingRef.current = true;

    appendUserTurn(trimmed);

    try {
      const stream = sendChatMessageStream(userId, sessionId, trimmed, generateRequestId());
      let displayRecommendations: Parameters<typeof finalizeAssistantTurn>[0] = [];
      for await (const ev of stream) {
        if (ev.event === "delta") {
          appendAssistantDelta(ev.data.text);
        } else if (ev.event === "final") {
          displayRecommendations = ev.data.response_state.display_recommendations;
        }
      }
      finalizeAssistantTurn(displayRecommendations);
    } catch (err) {
      console.error("[ChatbotPage] stream error", err);
      replaceLastAssistantMessage("오류가 발생했습니다. 다시 시도해 주세요.");
    } finally {
      setLoading(false);
      streamingRef.current = false;
    }
  }, [input, isLoading, userId, sessionId, appendUserTurn, appendAssistantDelta, finalizeAssistantTurn, replaceLastAssistantMessage, setLoading]);

  const handleHomeClick = () => {
    if (history.length > 0) {
      setShowExitModal(true);
    } else {
      onNavigateHome?.();
    }
  };

  const handleSaveAndExit = async () => {
    setExitLoading(true);
    try {
      await flushSession(sessionId, userId);
    } catch (err) {
      console.error("[ChatbotPage] flush error", err);
    } finally {
      clear();
      resetSession();
      setExitLoading(false);
      setShowExitModal(false);
      onNavigateHome?.();
    }
  };

  const handleExitWithoutSave = () => {
    clear();
    resetSession();
    setShowExitModal(false);
    onNavigateHome?.();
  };

  const lastTurn = history[history.length - 1];

  return (
    <DreamBackground variant="chatbot">
      <div className="chatbot-page">
        <GlassPanel className="chatbot-shell" intensity="strong">
          <ChatbotHeader userId={userId} onHomeClick={handleHomeClick} />

          <div className="chat-body">
            <ChatHistory history={history} isLoading={isLoading} />
            <div ref={bottomRef} />
          </div>

          {lastTurn?.display_recommendations?.length > 0 && (
            <RelatedRecommendationCards
              cards={lastTurn.display_recommendations}
              onAddToTaste={(contentId) => addToTaste({ userId, sessionId, contentId, requestId: generateRequestId() }).then(() => {})}
            />
          )}

          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isLoading}
          />
        </GlassPanel>

        {showExitModal && (
          <div className="exit-modal" role="dialog" aria-modal="true">
            <div className="exit-modal__backdrop" onClick={() => setShowExitModal(false)} />
            <div className="exit-modal__panel">
              <p className="exit-modal__message">세션을 종료하시겠습니까?</p>
              <div className="exit-modal__actions">
                <button
                  className="exit-modal__btn exit-modal__btn--save"
                  onClick={handleSaveAndExit}
                  disabled={exitLoading}
                >
                  저장하고 종료
                </button>
                <button
                  className="exit-modal__btn exit-modal__btn--discard"
                  onClick={handleExitWithoutSave}
                  disabled={exitLoading}
                >
                  저장하지 않고 이동
                </button>
                <button
                  className="exit-modal__btn exit-modal__btn--cancel"
                  onClick={() => setShowExitModal(false)}
                  disabled={exitLoading}
                >
                  취소
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DreamBackground>
  );
}
