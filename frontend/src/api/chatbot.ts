import type { ChatbotResponse, SessionHistoryResponse } from "../types";
import { apiClient } from "./client";

export async function sendChatMessage(
  userId: string,
  sessionId: string,
  userInput: string
): Promise<ChatbotResponse> {
  const res = await apiClient.post<ChatbotResponse>("/api/chatbot/respond", {
    user_id: userId,
    session_id: sessionId,
    user_input: userInput,
  });
  return res.data;
}

export async function fetchSessionHistory(
  sessionId: string,
  userId: string
): Promise<SessionHistoryResponse> {
  const res = await apiClient.get<SessionHistoryResponse>(`/api/sessions/${sessionId}/history`, {
    params: { user_id: userId },
  });
  return res.data;
}

export async function flushSession(sessionId: string, userId: string): Promise<void> {
  await apiClient.post(`/api/sessions/${sessionId}/flush`, null, {
    params: { user_id: userId },
  });
}
