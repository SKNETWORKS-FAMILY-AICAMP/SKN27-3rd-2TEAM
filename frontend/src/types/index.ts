// ─── Recommendation ───────────────────────────────────────────────────────────

export interface RecommendationCard {
  content_id: string;
  title: string;
  artist: string;
  album?: string;
  label?: string;
  genre?: string[];
  mood?: string[];
  display_reason: string;
}

export interface MainViewModel {
  status: string;
  page_type: string;
  user_id: string;
  taste_badges: string[];
  today_theme: string;
  character_message: string;
  personalized: RecommendationCard[];
  new_release: RecommendationCard[];
  discovery: RecommendationCard[];
  personalized_guide: string;
  debug?: Record<string, unknown>;
}

export interface MainRecommendationResponse {
  status: string;
  page_type: string;
  view_model: MainViewModel;
}

export interface MusicDetail {
  content_id: string;
  title: string;
  artist: string;
  album?: string | null;
  genre: string[];
  mood: string[];
  display_reason: string;
  evidence_summary: string;
  source: string;
}

export interface MusicDetailResponse {
  status: string;
  music_detail: MusicDetail;
}

// ─── Chatbot ──────────────────────────────────────────────────────────────────

export interface ChatDisplayRecommendation {
  content_id: string;
  title: string;
  artist: string;
  display_reason: string;
  label?: string;
  recommendation_category?: string;
}

export interface ResponseState {
  status: string;
  response_type: string;
  chatbot_response: string;
  display_recommendations: ChatDisplayRecommendation[];
  used_content_ids: string[];
}

export interface ChatbotResponse {
  status: string;
  response_state: ResponseState;
  latency_ms: number;
}

export interface ChatTurn {
  user_input: string;
  chatbot_response: string;
  display_recommendations: ChatDisplayRecommendation[];
  created_at: string;
}

// ─── Session ──────────────────────────────────────────────────────────────────

export interface SessionHistoryResponse {
  session_id: string;
  history: ChatTurn[];
}
