/**
 * sessionStore — 최소 상태만 보관
 * userId / sessionId는 앱 수명 동안 변경되지 않으므로 여기서만 관리한다.
 * sessionId는 마운트 시 생성하고 이후에는 바꾸지 않는다.
 */
import { create } from "zustand";

function generateSessionId(): string {
  return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

interface SessionState {
  userId: string;
  sessionId: string;
  setUserId: (id: string) => void;
  resetSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  userId: "user_001",
  sessionId: generateSessionId(),
  setUserId: (id) => set({ userId: id }),
  resetSession: () => set({ sessionId: generateSessionId() }),
}));
