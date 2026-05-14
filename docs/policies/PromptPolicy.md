# Prompt Policy

구현 기준: `app/prompts/`, `app/llm/openai_llm_client.py`

---

## 목적

LLM을 사용하는 모든 Agent의 프롬프트 설계 원칙과 허용 범위를 정의한다.

---

## 핵심 원칙

1. **LLM은 해석만 수행한다.**  
   LLM은 사용자 의도를 분류하고 자연어를 정규화하는 역할만 한다.

2. **시스템 권한은 deterministic validator가 가진다.**  
   LLM 출력은 반드시 enum/schema 검증을 통과해야 최종 사용된다.

3. **LLM은 추천 결과를 생성하지 않는다.**  
   content_id, title, artist, KAG_STATE, RAG_STATE를 LLM이 생성하는 것은 금지된다.

---

## LLM 적용 범위

| Agent | LLM 사용 여부 | 역할 |
|-------|-------------|------|
| InputPlannerAgent | optional | 사용자 입력 → intent/mood/genre 분류 |
| ResponseGenerator | 필수 | 추천 결과 → 자연어 응답 생성 |
| IntentAgent | 미사용 | rule-based 확정 |
| KagDispatchAgent | 미사용 | mock/real adapter 위임 |
| RagDispatchAgent | 미사용 | mock/real adapter 위임 |

---

## InputPlannerAgent 프롬프트 정책

- 파일: `app/prompts/input_planner_prompt.py`
- LLM은 다음 필드만 출력한다:
  - `intent_type`: 허용 enum 중 하나
  - `confidence`: 0.0 ~ 1.0
  - `normalized_query`: 검색에 적합한 정규화 문장
  - `detected_moods`: 허용 enum 내 값만
  - `detected_genres`: 허용 enum 내 값만
  - `detected_situations`: 허용 enum 내 값만
- enum 외 값이 포함되면 해당 필드를 필터링한다.
- LLM 호출 실패 또는 schema validation 실패 시 rule-based fallback을 사용한다.

### 허용 enum 목록

```
intent_type: personalized_recommendation, new_release_recommendation,
             discovery_recommendation, music_information,
             recommendation_reason, general_chat

detected_moods: calm, night, bright, clean

detected_genres: indie, dream_pop, ambient, rnb, electro_pop

detected_situations: late_night
```

---

## Fallback 정책

| 상황 | 동작 |
|------|------|
| OPENAI_API_KEY 없음 | 시작 시 rule-based로 자동 전환 |
| LLM 호출 오류 | 경고 로그 후 rule-based fallback |
| intent_type enum 불일치 | rule-based fallback |
| schema validation 실패 | rule-based fallback |

---

## 금지 사항

- LLM 프롬프트에 content_id, title, artist 생성을 요청하지 않는다.
- LLM 출력을 validator 없이 직접 사용하지 않는다.
- strict=True JSON schema 없이 LLM을 호출하지 않는다.
- temperature > 0.5로 설정하지 않는다 (현재 0.2).
- LLM은 display_reason의 곡, 아티스트, content_id를 변경하지 않는다.
- LLM은 raw evidence_summary, lyrics, Elasticsearch document를 그대로 복사하지 않는다.
- LLM display_reason 결과는 validator 통과 시에만 사용자 응답에 사용한다.

---

## 운영 관점

- LLM 모델 변경은 `RIMAS_LLM_MODEL` 환경 변수로 제어한다.
- 타임아웃은 `RIMAS_LLM_TIMEOUT_SECONDS` 환경 변수로 제어한다 (기본 30초).
- prod 환경에서는 `OPENAI_API_KEY`가 없으면 서버가 시작되지 않는다.
