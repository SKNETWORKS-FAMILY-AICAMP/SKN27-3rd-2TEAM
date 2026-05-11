import type { MusicDetailResponse } from "../types";
import { apiClient } from "./client";

export async function fetchMusicDetail(
  contentId: string,
  options?: { userId?: string; sessionId?: string; requestId?: string }
): Promise<MusicDetailResponse> {
  const res = await apiClient.get<MusicDetailResponse>(
    `/api/music/detail/${encodeURIComponent(contentId)}`,
    {
      params: {
        user_id: options?.userId,
        session_id: options?.sessionId,
        request_id: options?.requestId,
      },
    }
  );
  return res.data;
}
