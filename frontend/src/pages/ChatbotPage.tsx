/**
 * 챗봇 페이지
 *
 * 성능 규칙:
 *   - 마운트 시 히스토리 1회 로드 (React Query)
 *   - 메시지 전송은 useMutation (중복 전송은 isPending으로 차단)
 *   - chatStore.appendTurn으로 낙관적 업데이트 → 재렌더 최소화
 *   - 입력값은 지역 useState (store에 두지 않음 — 타이핑마다 전역 재렌더 방지)
 */
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, useCallback, useEffect, useRef } from "react";
import { fetchSessionHistory, sendChatMessage } from "../api/chatbot";
import { useChatStore } from "../stores/chatStore";
import { useSessionStore } from "../stores/sessionStore";
import { ChatHistory } from "../components/chatbot/ChatHistory";
import { ChatInput } from "../components/chatbot/ChatInput";
import { ChatbotHeader } from "../components/chatbot/ChatbotHeader";
import { RelatedRecommendationCards } from "../components/chatbot/RelatedRecommendationCards";

export function ChatbotPage() {
  const { userId, sessionId } = useSessionStore();
  const { history, isLoading, appendTurn, setHistory, setLoading } = useChatStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // 마운트 시 히스토리 1회 로드
  const { data: historyData } = useQuery({
    queryKey: ["session-history", sessionId],
    queryFn: () => fetchSessionHistory(sessionId, userId),
    staleTime: Infinity,  // 세션 수명 동안 재조회 없음
    retry: false,
  });

  useEffect(() => {
    if (historyData?.history) {
      setHistory(historyData.history);
    }
  }, [historyData, setHistory]);

  // 자동 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const mutation = useMutation({
    mutationFn: ({ userInput }: { userInput: string }) =>
      sendChatMessage(userId, sessionId, userInput),
    onMutate: () => setLoading(true),
    onSuccess: (data, variables) => {
      const rs = data.response_state;
      appendTurn(variables.userInput, rs.chatbot_response, rs.display_recommendations);
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
    mutation.mutate({ userInput: trimmed });
  }, [input, mutation]);

  const lastTurn = history[history.length - 1];

  return (
    <div className="chatbot-page">
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
    </div>
  );
}
