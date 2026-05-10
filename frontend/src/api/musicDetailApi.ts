import type { MusicDetailResponse } from "../types";
import { apiClient } from "./client";

export async function fetchMusicDetail(contentId: string): Promise<MusicDetailResponse> {
  const res = await apiClient.get<MusicDetailResponse>(
    `/api/music/detail/${encodeURIComponent(contentId)}`
  );
  return res.data;
}
