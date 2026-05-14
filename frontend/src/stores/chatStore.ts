/**
 * chatStore — 최소 상태만 보관
 *
 * 렌더링 규칙:
 *   - history 배열이 바뀔 때만 컴포넌트가 재렌더된다.
 *   - isLoading은 전송 중에만 true이다.
 *   - API 응답(response_state)은 store에 두지 않고 history에만 추가한다.
 *     (별도 state로 두면 중복 렌더링 발생)
 */
import { create } from "zustand";
import type { ChatDisplayRecommendation, ChatTurn } from "../types";

interface ChatState {
  history: ChatTurn[];
  isLoading: boolean;
  appendTurn: (
    userInput: string,
    chatbotResponse: string,
    displayRecommendations: ChatDisplayRecommendation[]
  ) => void;
  appendUserTurn: (userInput: string) => void;
  appendAssistantPlaceholder: () => void;
  appendAssistantDelta: (delta: string) => void;
  finalizeAssistantTurn: (displayRecommendations: ChatDisplayRecommendation[]) => void;
  replaceLastAssistantMessage: (message: string) => void;
  setHistory: (turns: ChatTurn[]) => void;
  setLoading: (v: boolean) => void;
  clear: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  history: [],
  isLoading: false,

  appendTurn: (userInput, chatbotResponse, displayRecommendations) =>
    set((state) => ({
      history: [
        ...state.history,
        {
          user_input: userInput,
          chatbot_response: chatbotResponse,
          display_recommendations: displayRecommendations,
          created_at: new Date().toISOString(),
        },
      ],
    })),

  appendUserTurn: (userInput) =>
    set((state) => ({
      history: [
        ...state.history,
        { user_input: userInput, chatbot_response: "", display_recommendations: [], created_at: new Date().toISOString() },
      ],
    })),

  appendAssistantPlaceholder: () =>
    set((state) => ({
      history: [
        ...state.history,
        { user_input: "", chatbot_response: "", display_recommendations: [], created_at: new Date().toISOString() },
      ],
    })),

  appendAssistantDelta: (delta) =>
    set((state) => {
      if (state.history.length === 0) return state;
      const updated = [...state.history];
      const last = { ...updated[updated.length - 1] };
      last.chatbot_response += delta;
      updated[updated.length - 1] = last;
      return { history: updated };
    }),

  finalizeAssistantTurn: (displayRecommendations) =>
    set((state) => {
      if (state.history.length === 0) return state;
      const updated = [...state.history];
      const last = { ...updated[updated.length - 1] };
      last.display_recommendations = displayRecommendations;
      updated[updated.length - 1] = last;
      return { history: updated };
    }),

  replaceLastAssistantMessage: (message) =>
    set((state) => {
      if (state.history.length === 0) return state;
      const updated = [...state.history];
      const last = { ...updated[updated.length - 1] };
      last.chatbot_response = message;
      updated[updated.length - 1] = last;
      return { history: updated };
    }),

  setHistory: (turns) => set({ history: turns }),
  setLoading: (v) => set({ isLoading: v }),
  clear: () => set({ history: [], isLoading: false }),
}));
