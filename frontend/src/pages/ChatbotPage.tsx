/**
 * 챗봇 페이지.
 *
 * API 호출, 세션 히스토리 로드, response_state 처리 흐름은 기존 계약을 유지한다.
 */
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, useCallback, useEffect, useRef } from "react";
import { fetchSessionHistory, sendChatMessage } from "../api/chatbot";
import { DreamBackground } from "../components/background/DreamBackground";
import { ChatHistory } from "../components/chatbot/ChatHistory";
import { ChatInput } from "../components/chatbot/ChatInput";
import { ChatbotHeader } from "../components/chatbot/ChatbotHeader";
import { RelatedRecommendationCards } from "../components/chatbot/RelatedRecommendationCards";
import { GlassPanel } from "../components/ui/GlassPanel";
import { useChatStore } from "../stores/chatStore";
import { useSessionStore } from "../stores/sessionStore";
import { generateRequestId } from "../utils/requestId";

export function ChatbotPage() {
  const { userId, sessionId } = useSessionStore();
  const { history, isLoading, appendTurn, setHistory, setLoading } = useChatStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

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

  const mutation = useMutation({
    mutationFn: ({ userInput, requestId }: { userInput: string; requestId: string }) =>
      sendChatMessage(userId, sessionId, userInput, requestId),
    onMutate: () => setLoading(true),
    onSuccess: (data, variables) => {
      const rs = data.response_state;
      appendTurn(variables.userInput, rs.chatbot_response, rs.display_recommendations);
      if (data.session_degraded) {
        console.warn("[ChatbotPage] session_degraded: Redis session is temporarily unstable.");
      }
      setLoading(false);
    },
    onError: (err) => {
      console.error("[ChatbotPage] send error", err);
      setLoading(false);
    },
  });

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || mutation.isPending) return;
    setInput("");
    mutation.mutate({ userInput: trimmed, requestId: generateRequestId() });
  }, [input, mutation]);

  const lastTurn = history[history.length - 1];

  return (
    <DreamBackground variant="chatbot">
      <div className="chatbot-page">
        <GlassPanel className="chatbot-shell" intensity="strong">
          <ChatbotHeader userId={userId} />

          <div className="chat-body">
            <ChatHistory history={history} />
            <div ref={bottomRef} />
          </div>

          {lastTurn?.display_recommendations?.length > 0 && (
            <RelatedRecommendationCards cards={lastTurn.display_recommendations} />
          )}

          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isLoading}
          />
        </GlassPanel>
      </div>
    </DreamBackground>
  );
}
