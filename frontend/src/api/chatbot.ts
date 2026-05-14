import type { ChatbotResponse, ResponseState, SessionHistoryResponse } from "../types";
import { apiClient } from "./client";

const BASE_URL = (import.meta as unknown as { env: Record<string, string> }).env?.VITE_API_URL ?? "";

export async function sendChatMessage(
  userId: string,
  sessionId: string,
  userInput: string,
  requestId: string
): Promise<ChatbotResponse> {
  const res = await apiClient.post<ChatbotResponse>("/api/chatbot/respond", {
    user_id: userId,
    session_id: sessionId,
    user_input: userInput,
    request_id: requestId,
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

export async function clearSession(sessionId: string, userId: string): Promise<void> {
  await apiClient.delete(`/api/sessions/${sessionId}`, {
    params: { user_id: userId },
  });
}

export type StreamEvent =
  | { event: "delta"; data: { text: string } }
  | { event: "final"; data: { status: string; response_state: ResponseState; latency_ms: number } }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { message: string } };

export async function* sendChatMessageStream(
  userId: string,
  sessionId: string,
  userInput: string,
  requestId: string
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE_URL}/api/chatbot/respond/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      user_input: userInput,
      request_id: requestId,
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`stream request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      let eventType = "";
      let dataStr = "";
      for (const line of lines) {
        if (line.startsWith("event: ")) eventType = line.slice(7).trim();
        if (line.startsWith("data: ")) dataStr = line.slice(6).trim();
      }
      if (eventType && dataStr) {
        try {
          yield { event: eventType, data: JSON.parse(dataStr) } as StreamEvent;
        } catch {
          // malformed SSE chunk — skip
        }
      }
    }
  }
}
