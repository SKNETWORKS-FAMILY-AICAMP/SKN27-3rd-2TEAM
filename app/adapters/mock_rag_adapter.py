from app.adapters.rag_adapter import RagAdapter


class MockRagAdapter(RagAdapter):
    def build_state(self, kag_state):
        if not kag_state:
            raise ValueError("kag_state is required")

        return {
            "status": "success",
            "recommendation_context": {
                "context_type": kag_state["recommendation_goal"]["primary_goal"],
                "base_context": "rnb/indie 취향과 calm/night 분위기를 기준으로 추천 근거를 제공한다.",
                "source_type": "mock_music_catalog",
            },
            "recommended_content_evidence": [
                {
                    "content_id": "track_001",
                    "title": "Midnight Loop",
                    "artist": "Nova Lane",
                    "album": "Night Sketch",
                    "genre": ["rnb", "indie"],
                    "mood": ["calm", "night"],
                    "tempo": "medium",
                    "release_type": "existing_catalog",
                    "recommendation_category": "personalized_match",
                    "evidence_summary": "기존 rnb/indie 취향과 calm/night 분위기에 직접 연결되는 곡이다.",
                    "match_reason": {
                        "genre_match": True,
                        "mood_match": True,
                        "tempo_match": True,
                        "new_taste_expansion": False,
                    },
                },
                {
                    "content_id": "track_002",
                    "title": "Soft Orbit",
                    "artist": "Luna Field",
                    "album": "Orbit Notes",
                    "genre": ["dream_pop", "ambient"],
                    "mood": ["calm", "night", "soft"],
                    "tempo": "slow",
                    "release_type": "existing_catalog",
                    "recommendation_category": "discovery_candidate",
                    "evidence_summary": "calm/night 분위기를 유지하면서 dream pop 계열로 넓혀볼 수 있는 곡이다.",
                    "match_reason": {
                        "genre_match": False,
                        "mood_match": True,
                        "tempo_match": False,
                        "new_taste_expansion": True,
                    },
                },
                {
                    "content_id": "track_003",
                    "title": "Fresh Signal",
                    "artist": "Mira Tone",
                    "album": "Updated Signal",
                    "genre": ["indie", "electro_pop"],
                    "mood": ["bright", "clean"],
                    "tempo": "medium",
                    "release_type": "new_release",
                    "recommendation_category": "new_release",
                    "evidence_summary": "최근 업데이트된 곡 중 indie 선호와 일부 연결되는 곡이다.",
                    "match_reason": {
                        "genre_match": True,
                        "mood_match": False,
                        "tempo_match": True,
                        "new_taste_expansion": True,
                    },
                },
            ],
            "recommendation_reason": {
                "summary": "기존 개인화 추천을 기준으로 최신곡과 안전한 취향 탐색 후보를 함께 구성했다.",
                "reason_items": [
                    "기존 rnb/indie 취향과 연결되는 곡을 포함했다.",
                    "calm/night 분위기를 유지하면서 확장 가능한 곡을 포함했다.",
                    "최근 업데이트된 곡 중 기존 취향과 일부 맞는 곡을 포함했다.",
                ],
            },
            "information_evidence": [
                {
                    "info_id": "genre_dream_pop_001",
                    "info_type": "genre",
                    "title": "dream_pop",
                    "summary": "부드럽고 몽환적인 분위기가 특징인 pop 계열 장르다.",
                }
            ],
            "recommendation_scripts": {
                "dj_intro": "기존에 좋아하던 분위기는 유지하면서 조금 새로운 결의 음악을 골라봤어요.",
                "personalized_message": "먼저 익숙하게 들을 수 있는 곡을 추천할게요.",
                "new_release_message": "최근 업데이트된 곡 중에서도 취향과 연결되는 곡을 함께 넣었어요.",
                "discovery_message": "새로운 취향을 시도하고 싶다면 이 곡부터 시작해볼 수 있어요.",
                "fallback_message": "지금은 충분한 추천 근거가 부족해 기본 안내만 제공할게요.",
            },
        }
