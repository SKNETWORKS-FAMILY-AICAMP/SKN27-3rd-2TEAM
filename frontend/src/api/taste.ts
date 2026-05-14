import type { TasteEventResponse } from "../types";
import { apiClient } from "./client";

export async function addToTaste(params: {
  userId: string;
  sessionId: string;
  contentId: string;
  requestId: string;
}): Promise<TasteEventResponse> {
  const res = await apiClient.post<TasteEventResponse>("/api/taste/events", {
    user_id: params.userId,
    session_id: params.sessionId,
    content_id: params.contentId,
    event_type: "add_to_taste",
    source: "music_detail_modal",
    request_id: params.requestId,
  });
  return res.data;
}
