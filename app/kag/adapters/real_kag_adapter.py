from app.kag.adapters.kag_adapter import KagAdapter
from app.kag.connection import Neo4j_Connection
from app.kag.constant import KagQueryTemplateConstants
from app.kag.querys import KagQueryTools


class RealKagAdapter(KagAdapter):
    """Neo4j 기반 실제 KAG 어댑터.

    LLM 없이 입력 조건을 deterministic 규칙으로 쿼리에 매핑하고,
    Neo4j row를 기존 KAG_STATE 계약으로 변환한다.
    """

    def __init__(self, conn=None, query_tools=KagQueryTools):
        self._conn = conn
        self._query_tools = query_tools

    def build_state(
        self,
        user_id: str,
        user_input: str,
        session_context: dict,
        limit: int = 10,
    ) -> dict:
        if not user_id:
            raise ValueError("user_id is required")

        safe_limit = self._normalize_limit(limit)
        conditions = self._extract_conditions(user_input, session_context or {})
        query_key, params = self._select_query(conditions, safe_limit)
        rows = self._query_tools.execute(query_key, params, self._get_conn())
        excluded_nodes = self._build_excluded_nodes(session_context or {})

        primary_goal = self._decide_primary_goal(user_input)
        category = self._decide_category(primary_goal)
        route = self._decide_route(primary_goal)
        target_section = self._decide_target_section(category)
        matched_nodes = self._build_matched_nodes(conditions)

        if not rows:
            return {
                "status": "success",
                "recommendation_goal": {"primary_goal": primary_goal},
                "recommended_content_ids": [],
                "recommendation_category": category,
                "route": route,
                "target_section": target_section,
                "traversal_reason": "neo4j traversal returned no candidates",
                "matched_nodes": matched_nodes,
                "excluded_nodes": excluded_nodes,
                "candidate_tracks": [],
                "diversity_metadata": {"source": "neo4j", "degraded": True},
            }

        candidate_tracks = self._filter_candidate_tracks(
            self._map_candidate_tracks(rows),
            excluded_nodes,
        )[:safe_limit]
        recommended_content_ids = [track["content_id"] for track in candidate_tracks]

        return {
            "status": "success",
            "recommendation_goal": {"primary_goal": primary_goal},
            "recommended_content_ids": recommended_content_ids,
            "recommendation_category": category,
            "route": route,
            "target_section": target_section,
            "traversal_reason": f"neo4j deterministic traversal via {query_key}",
            "matched_nodes": matched_nodes,
            "excluded_nodes": excluded_nodes,
            "candidate_tracks": candidate_tracks,
            "diversity_metadata": {
                "source": "neo4j",
                "query_key": query_key,
                "candidate_count": len(candidate_tracks),
            },
        }

    def _get_conn(self):
        if self._conn is None:
            self._conn = Neo4j_Connection()
        return self._conn

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        try:
            parsed = int(limit)
        except (TypeError, ValueError):
            parsed = 10
        return max(1, min(parsed, 50))

    @staticmethod
    def _first_value(values) -> str | None:
        if not values:
            return None
        if isinstance(values, str):
            value = values.strip()
            return value or None
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    def _extract_conditions(self, user_input: str, session_context: dict) -> dict:
        text = (user_input or "").lower()
        return {
            "genre": (
                self._first_value(session_context.get("preferred_genres"))
                or self._first_value(session_context.get("recent_genres"))
                or self._detect_keyword(text, ("indie", "pop", "rock", "rnb", "hip hop", "edm", "latin"))
            ),
            "mood": (
                self._first_value(session_context.get("recent_moods"))
                or self._detect_keyword(text, ("calm", "night", "bright", "energetic", "sad", "focus"))
            ),
            "situation": self._detect_keyword(
                text,
                ("exercise", "commute", "focus", "study", "drive", "travel", "workout", "운동", "출근", "집중", "드라이브"),
            ),
            "weather": self._detect_keyword(text, ("rain", "sunny", "snow", "cloudy", "비", "맑음", "눈", "흐림")),
        }

    @staticmethod
    def _detect_keyword(text: str, keywords: tuple[str, ...]) -> str | None:
        for keyword in keywords:
            if keyword in text:
                return keyword
        return None

    @staticmethod
    def _select_query(conditions: dict, limit: int) -> tuple[str, dict]:
        active_conditions = {key: value for key, value in conditions.items() if value}
        if len(active_conditions) >= 2:
            return (
                KagQueryTemplateConstants.Q_REC_008,
                {
                    "genre": conditions.get("genre"),
                    "mood": conditions.get("mood"),
                    "situation": conditions.get("situation"),
                    "weather": conditions.get("weather"),
                    "limit": limit,
                },
            )
        if conditions.get("genre"):
            return KagQueryTemplateConstants.Q_REC_001, {"genre": conditions["genre"], "limit": limit}
        if conditions.get("situation"):
            return KagQueryTemplateConstants.Q_REC_003, {"situation": conditions["situation"], "limit": limit}
        if conditions.get("weather"):
            return KagQueryTemplateConstants.Q_REC_004, {"weather": conditions["weather"], "limit": limit}
        return KagQueryTemplateConstants.Q_REC_006, {"genre": None, "subgenre": None, "artist": None, "limit": limit}

    @staticmethod
    def _build_matched_nodes(conditions: dict) -> list[dict]:
        return [
            {"type": key, "value": value}
            for key, value in conditions.items()
            if value
        ]

    @staticmethod
    def _build_excluded_nodes(session_context: dict) -> list[dict]:
        nodes = []
        for artist in session_context.get("disliked_artists", []) or []:
            if artist:
                nodes.append({"type": "artist", "value": artist})
        for track in session_context.get("disliked_tracks", []) or []:
            if track:
                nodes.append({"type": "track", "value": track})
        for genre in session_context.get("disliked_genres", []) or []:
            if genre:
                nodes.append({"type": "genre", "value": genre})
        return nodes

    @staticmethod
    def _filter_candidate_tracks(candidates: list[dict], excluded_nodes: list[dict]) -> list[dict]:
        excluded_artists = {node["value"] for node in excluded_nodes if node.get("type") == "artist"}
        excluded_tracks = {node["value"] for node in excluded_nodes if node.get("type") == "track"}
        excluded_genres = {node["value"] for node in excluded_nodes if node.get("type") == "genre"}
        return [
            candidate
            for candidate in candidates
            if candidate.get("content_id") not in excluded_tracks
            and candidate.get("artist") not in excluded_artists
            and candidate.get("genre") not in excluded_genres
            and candidate.get("subgenre") not in excluded_genres
        ]

    @staticmethod
    def _map_candidate_tracks(rows: list[dict]) -> list[dict]:
        seen = set()
        candidates = []
        for row in rows:
            track_id = row.get("track_id")
            if not track_id or track_id in seen:
                continue
            seen.add(track_id)

            candidate = {"content_id": track_id}
            field_map = {
                "track_name": "title",
                "track_artist": "artist",
                "genre": "genre",
                "subgenre": "subgenre",
                "popularity": "popularity",
                "recommendation_score": "score",
                "matched_mood": "matched_mood",
                "matched_situation": "matched_situation",
                "matched_weather": "matched_weather",
                "matched_count": "matched_count",
            }
            for source, target in field_map.items():
                if source in row and row[source] is not None:
                    candidate[target] = row[source]
            candidates.append(candidate)
        return candidates

    @staticmethod
    def _decide_primary_goal(user_input: str) -> str:
        text = user_input or ""
        if "왜" in text or "이유" in text:
            return "recommendation_reason_question"
        if "최신" in text or "새로 나온" in text or "신곡" in text:
            return "new_release_recommendation"
        if "비슷" in text:
            return "similar_taste_recommendation"
        if "취향" in text or "새로운" in text:
            return "new_taste_discovery"
        return "personalized_recommendation"

    @staticmethod
    def _decide_category(primary_goal: str) -> str:
        if primary_goal == "new_release_recommendation":
            return "new_release"
        if primary_goal == "new_taste_discovery":
            return "discovery_candidate"
        return "personalized_match"

    @staticmethod
    def _decide_route(primary_goal: str) -> str:
        if primary_goal == "new_release_recommendation":
            return "new_release"
        if primary_goal == "new_taste_discovery":
            return "safe_discovery"
        return "personalized"

    @staticmethod
    def _decide_target_section(category: str) -> str:
        if category == "new_release":
            return "new_release_section"
        if category == "discovery_candidate":
            return "discovery_section"
        return "personalized_section"
