import type { MainRecommendationResponse } from "../types";
import { apiClient } from "./client";

export async function fetchMainRecommendations(
  userId: string,
  sessionId: string
): Promise<MainRecommendationResponse> {
  const res = await apiClient.get<MainRecommendationResponse>("/api/recommendations/main", {
    params: { user_id: userId, session_id: sessionId },
  });
  return res.data;
}
