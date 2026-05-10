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

  setHistory: (turns) => set({ history: turns }),
  setLoading: (v) => set({ isLoading: v }),
  clear: () => set({ history: [], isLoading: false }),
}));
