# 추천 품질 업데이트 의사결정 기록

## 1. 문서 목적

이 문서는 챗봇 추천 품질 업데이트와 관련해 현재 발견된 문제, 기존 설계서와의 관계, 이미 내려진 의사결정, 앞으로 구현 전에 확정해야 할 선택지를 정리한다.

구현 기준 문서는 다음 설계서다.

- `docs/superpowers/specs/2026-05-14-chatbot-recommendation-quality-update-design.md`

기존 관련 문서는 다음과 같다.

- `docs/superpowers/specs/2026-05-14-chatbot-taste-feedback-streaming-design.md`
- `docs/superpowers/plans/2026-05-14-chatbot-taste-feedback-streaming.md`
- `docs/policies/RecommendationPolicy.md`
- `docs/policies/PromptPolicy.md`
- `docs/rimas_v_4_integrated_design_updated_final_.md`

## 2. 전체 상황 요약

현재 RIMAS 추천 파이프라인은 사용자의 명시적 긍정 취향을 Redis session context와 taste event로 저장하는 흐름은 갖고 있다. 반면 사용자가 싫다고 말한 아티스트나 곡을 부정 취향으로 저장하고 추천에서 제외하는 정책은 기존 taste feedback 설계서에서 제외 범위로 분류되어 있었다.

또한 추천 결과 생성 과정에서 다음 문제가 확인되었다.

1. 사용자가 싫다고 말한 아티스트나 곡이 이후 추천에서 다시 나올 수 있다.
2. RAG evidence가 같은 `content_id`를 여러 번 포함하면 메인 추천 화면에 같은 노래가 반복될 수 있다.
3. 사용자가 "1곡", "두 곡"처럼 요청 수를 말해도 최종 추천 개수에 반영되지 않는다.
4. 메인 추천 화면의 `new_release`, `discovery` 섹션이 RAG 결과에 따라 빈 배열로 남을 수 있다.
5. Elasticsearch evidence의 `content`나 `evidence_summary`가 추천 이유로 그대로 노출될 수 있어, 가사 원문 또는 긴 raw document가 사용자 화면에 보일 위험이 있다.

이번 업데이트 설계서는 기존 구조를 갈아엎지 않고, KAG/RAG/Recommendation/ResponseGenerator 흐름 위에 필요한 계약을 확장하는 방식으로 문제를 해결한다.

## 3. 기존 설계서와의 관계

### 3.1 충돌 지점

기존 `2026-05-14-chatbot-taste-feedback-streaming-design.md`는 "싫어요, 차단, 제외 추천 정책"을 제외 범위로 명시했다.

따라서 새 설계서가 부정 취향 필터링을 포함하는 것은 기존 문서를 그대로 기준으로 보면 충돌이다.

### 3.2 결정

이번 작업은 기존 taste feedback 설계서를 직접 수정하지 않는다.

대신 새 문서인 `2026-05-14-chatbot-recommendation-quality-update-design.md`를 기존 설계의 업데이트 설계서로 승인하고, 기존 제외 범위를 변경하는 방식으로 진행한다.

### 3.3 이유

기존 문서를 덮어쓰면 이미 구현된 `add_to_taste`, session flush, streaming 범위와 새 추천 품질 정책이 섞인다. 별도 업데이트 설계서로 분리하면 변경 이력이 명확하고, 어떤 요구사항이 나중에 추가 승인되었는지 추적하기 쉽다.

## 4. 문제별 현재 상태와 결정

## 4.1 싫어하는 아티스트/곡 무시 문제

### 현재 상태

현재 세션 컨텍스트에는 긍정 취향에 해당하는 `recent_genres`, `recent_artists`, `recent_moods`, `selected_tracks`가 있다.

하지만 부정 취향에 해당하는 `disliked_artists`, `disliked_tracks` 계약은 없다.

Input Planner도 "싫어", "별로", "추천하지 마", "빼줘", "제외해줘" 같은 표현을 별도 부정 취향으로 추출하지 않는다.

KAG_STATE에는 `excluded_nodes` 필드가 있지만, 현재 adapter는 이를 실질적으로 채우거나 필터링에 사용하지 않는다.

### 결정된 방향

부정 취향은 긍정 취향과 분리해 저장한다.

SESSION_CONTEXT에 다음 필드를 추가한다.

```json
{
  "disliked_artists": ["Billie Eilish"],
  "disliked_tracks": ["track_999"]
}
```

KAG_INPUT constraints에는 다음 필드를 추가한다.

```json
{
  "excluded_artists": ["Billie Eilish"],
  "excluded_tracks": ["track_999"]
}
```

KAG_STATE에는 다음처럼 제외 노드를 기록한다.

```json
{
  "excluded_nodes": [
    {"type": "artist", "value": "Billie Eilish"},
    {"type": "track", "value": "track_999"}
  ]
}
```

추천 후보는 KAG와 RAG 양쪽에서 방어적으로 필터링한다.

### 결정 이유

사용자가 명시적으로 싫다고 말한 항목은 단순 선호도가 낮은 항목이 아니라 제외 조건이다. 따라서 ranking score를 낮추는 방식이 아니라 후보군에서 제거하는 방식이 더 명확하다.

### 아직 남은 의사결정

1. 사용자가 "전에 싫다던 것도 다시 추천해줘"라고 말했을 때 해제를 지원할지 결정해야 한다.

현재 업데이트 설계서의 결정은 다음과 같다.

- DB schema 확장을 이번 범위에 포함한다.
- 부정 취향은 PostgreSQL에 영구 저장하고 새 세션 hydrate 시 SESSION_CONTEXT에 병합한다.
- 부정 취향 해제는 이번 범위에서 제외한다.
- 부정 취향 추출은 장르 부정 표현을 먼저 분리하고, 남은 대상은 `music_catalog` 정확 매칭으로 아티스트와 곡을 구분한다.
- 입력 부정 표현 앞의 마지막 대화 구간에 `pop`, `팝`, `rnb` 같은 허용 장르가 포함되면 `disliked_genres`에 저장한다.
- 입력 부정 표현 앞의 대상이 `artist`와 정확히 일치하면 `disliked_artists`에 저장한다.
- 입력 부정 표현 앞의 대상이 `title`과 정확히 일치하면 일치하는 모든 `content_id`를 `disliked_tracks`에 저장한다.
- `artist`와 `title`이 모두 일치하면 아티스트 제외를 우선한다.
- 장르로도, 카탈로그로도 정확히 매칭되지 않는 부정 대상은 영구 저장하지 않는다.

## 4.2 같은 노래 3곡 문제

### 현재 상태

챗봇 최종 추천을 만드는 `RecommendationAgent`는 `content_id` 기준 중복 제거를 일부 수행한다.

하지만 메인 추천 화면을 만드는 `MainRecommendationService`는 RAG evidence를 섹션에 그대로 넣는다. Real RAG는 한 곡당 여러 evidence를 반환할 수 있기 때문에 같은 `content_id`가 여러 번 표시될 수 있다.

### 결정된 방향

중복 기준은 제목이나 아티스트명이 아니라 `content_id`로 한다.

같은 `content_id`가 같은 섹션 안에서 반복되면 한 번만 표시한다.

fallback으로 채우는 섹션에서도 이미 다른 섹션에 표시된 `content_id`는 제외한다.

### 결정 이유

곡의 실제 식별자는 `content_id`다. 같은 제목을 가진 다른 곡이 있을 수 있고, 같은 곡에 여러 evidence가 붙을 수 있으므로 제목 기반 dedup은 부정확하다.

### 아직 남은 의사결정

1. 같은 `content_id`가 여러 섹션에 동시에 적합할 때 어느 섹션을 우선할지 결정해야 한다.
2. 중복 제거 후 섹션 개수가 부족하면 fallback을 즉시 채울지, 부족한 상태로 둘지 결정해야 한다.

현재 업데이트 설계서의 결정은 다음과 같다.

- RAG evidence의 기존 category 우선순위를 유지한다.
- fallback은 이미 표시된 `content_id`를 제외하고 부족한 섹션을 채운다.

## 4.3 요청 곡 수 미반영 문제

### 현재 상태

KAG_INPUT constraints에는 `max_candidates`가 있지만 Input Planner가 항상 `10`으로 설정한다.

IntentState에는 `requested_count`가 없다.

RecommendationAgent는 항상 정책 기본값인 `MAX_SELECTED_RECOMMENDATIONS` 기준으로 결과를 자른다.

### 결정된 방향

Input Planner가 사용자의 요청 곡 수를 `requested_count`로 추출한다.

지원 표현은 다음과 같다.

- `1곡`, `한 곡`, `하나`
- `2곡`, `두 곡`, `둘`
- `3곡`, `세 곡`, `셋`

`requested_count`는 KAG_INPUT constraints의 `max_candidates`와 RecommendationAgent의 최종 slice에 모두 반영한다.

### 결정 이유

후보 조회 단계와 최종 선택 단계가 같은 요청 수를 공유해야 불필요한 후보 조회를 줄이고 최종 응답도 사용자 의도와 맞는다.

### 아직 남은 의사결정

1. 사용자가 `10곡 추천해줘`처럼 기본 정책보다 큰 수를 요청하면 허용할지 제한할지 결정해야 한다.
2. `몇 곡만`, `조금만`, `많이 추천해줘`처럼 모호한 표현을 숫자로 해석할지 결정해야 한다.

현재 업데이트 설계서의 결정은 다음과 같다.

- `requested_count`는 1 이상 `MAX_SELECTED_RECOMMENDATIONS` 이하로 제한한다.
- 모호한 수량 표현은 이번 범위에서 숫자로 해석하지 않는다.

## 4.4 신규 발매/다양한 장르 섹션 비어 있음 문제

### 현재 상태

Real RAG는 현재 evidence의 `recommendation_category`를 `personalized_match`로 고정한다.

메인 추천 화면은 RAG evidence의 category를 기준으로 `personalized`, `new_release`, `discovery` 섹션을 나눈다.

따라서 RAG 결과에 `new_release`, `discovery_candidate`가 없으면 해당 섹션은 빈 배열이 된다.

### 결정된 방향

RAG 결과가 섹션을 채우지 못하면 DB fallback으로 채운다.

현재 `music_catalog`에는 `release_date`, `popularity` 컬럼이 없으므로 다음 기준만 사용한다.

신규 발매 fallback:

```sql
WHERE release_type = 'new_release'
ORDER BY created_at DESC, content_id ASC
```

다양한 장르 fallback:

```sql
WHERE recommendation_category = 'discovery_candidate'
ORDER BY created_at DESC, content_id ASC
```

fallback 결과는 다음을 제외한다.

- 이미 화면에 표시된 `content_id`
- `disliked_tracks`에 포함된 `content_id`
- `disliked_artists`에 포함된 artist

### 결정 이유

화면은 처음 진입하든 나중에 진입하든 비어 있으면 안 된다. 다만 현재 DB schema에 없는 popularity나 release_date를 가정하면 구현이 문서와 스키마를 벗어나므로 사용 가능한 필드만 사용한다.

### 아직 남은 의사결정

1. fallback 결과가 DB에도 없을 때 빈 섹션을 허용할지, mock/static fallback을 둘지 결정해야 한다.
2. discovery fallback에서 사용자의 선호 장르와 다른 장르를 우선할지, 선호 장르와 가까운 곡을 우선할지 결정해야 한다.
3. 섹션별 목표 개수를 몇 개로 할지 결정해야 한다.

현재 업데이트 설계서의 결정은 다음과 같다.

- DB에 후보가 없으면 해당 섹션은 빈 배열일 수 있다.
- discovery fallback은 `recommendation_category = 'discovery_candidate'`를 우선한다.
- 섹션별 목표 개수는 구현 계획에서 현재 UI 기대값과 테스트 기준에 맞춰 확정한다.

## 4.5 추천 이유에 가사 원문 노출 문제

### 현재 상태

Real RAG는 Elasticsearch hit의 `content`를 `evidence_summary`로 넣는다.

RecommendationAgent는 `evidence_summary`를 그대로 `display_reason`에 넣는다.

따라서 Elasticsearch `content`가 가사 원문이나 긴 raw document라면 사용자에게 그대로 노출될 수 있다.

기존 통합 설계서는 `display_reason 임의 생성 금지`, `title, artist, display_reason 임의 변경 금지`를 강조한다. 동시에 PromptPolicy는 LLM이 content_id, title, artist를 생성하지 못하도록 제한한다.

### 결정된 방향

raw `evidence_summary`를 `display_reason`에 직접 복사하지 않는다.

추천 이유는 다음 필드 기반의 짧은 한국어 설명으로 생성한다.

- title
- artist
- genre
- mood
- recommendation_category
- release_type
- match_reason

LLM을 사용할 때도 곡, 아티스트, content_id를 생성하거나 바꾸지 않는다.

LLM은 이미 선택된 추천 결과에 대한 설명 문장만 정리한다.

LLM이 반환한 추천 이유는 `content_id`, `title`, `artist`가 선택된 추천 결과와 일치하고 `DisplayReasonValidator`를 통과할 때만 사용한다.

LLM을 사용할 수 없는 환경에서는 로컬 fallback 설명을 생성한다.

### 결정 이유

추천 이유는 사용자에게 보여주는 설명이지 raw evidence dump가 아니다. 가사 원문 또는 긴 본문을 그대로 노출하면 사용자 경험과 저작권/품질 측면 모두에서 위험하다.

### 아직 남은 의사결정

1. `display_reason 임의 생성 금지`라는 기존 문구를 어떻게 해석할지 확정해야 한다.
2. evidence_summary를 완전히 숨길지, 내부 debug에는 유지할지 결정해야 한다.

현재 업데이트 설계서의 결정은 다음과 같다.

- `display_reason 임의 생성 금지`는 "곡, 아티스트, content_id를 생성하지 말라"는 의미로 제한 해석한다.
- 사용자 노출용 `display_reason`은 raw evidence 복사가 아니라 정제된 설명으로 만든다.
- LLM이 생성한 설명은 `DisplayReasonValidator` 검증을 통과할 때만 사용한다.
- 검증 실패 시 deterministic draft를 사용한다.
- 내부 RAG_STATE의 `evidence_summary`는 유지하되 사용자 노출 경로에서는 직접 사용하지 않는다.

## 5. 전역 의사결정 목록

## 5.1 이미 결정된 사항

1. 새 설계서는 기존 taste feedback 설계서를 덮어쓰지 않고 업데이트 설계서로 승인한다.
2. 부정 취향은 긍정 취향과 분리한다.
3. 부정 취향은 추천 후보에서 제거한다.
4. 부정 취향은 PostgreSQL에 영구 저장한다.
5. 중복 추천 기준은 `content_id`다.
6. 요청 곡 수는 `requested_count`로 명시한다.
7. 요청 곡 수는 후보 조회와 최종 추천 선택에 모두 반영한다.
8. 메인 추천 섹션은 RAG 결과가 없으면 DB fallback으로 채운다.
9. 현재 DB schema에 없는 `release_date`, `popularity`는 사용하지 않는다.
10. 추천 이유는 raw evidence를 그대로 노출하지 않는다.
11. LLM은 추천 결과 자체를 생성하지 않고 설명만 생성한다.
12. LLM 추천 이유는 validator를 통과할 때만 사용한다.

## 5.2 구현 전에 확정할 사항

1. 부정 취향 해제 정책을 이번 범위에 포함할지
2. 사용자가 `MAX_SELECTED_RECOMMENDATIONS`보다 큰 수를 요청할 때의 응답 방식
3. fallback 섹션별 목표 개수
4. fallback DB 후보도 없을 때 UI에 빈 섹션을 허용할지
5. 기존 통합 설계서의 `display_reason 임의 생성 금지` 문구를 문서상 갱신할지

## 6. 권장 결정안

구현 복잡도와 기존 계약 안정성을 기준으로 다음 결정을 권장한다.

1. 부정 취향은 Redis session context와 PostgreSQL에 모두 저장한다.
2. 부정 취향 해제는 이번 범위에서 제외한다.
3. 요청 곡 수는 1 이상 `MAX_SELECTED_RECOMMENDATIONS` 이하로 clamp한다.
4. fallback 섹션별 목표 개수는 기존 UI 카드 표시 기준에 맞춰 3개로 시작한다.
5. fallback DB 후보가 없으면 해당 섹션은 빈 배열을 허용하되, DB에 후보가 있는데 비는 경우는 버그로 본다.
6. `display_reason`은 deterministic draft를 먼저 만들고, LLM 후처리는 validator 통과 시에만 사용한다.
7. 기존 통합 설계서의 `display_reason 임의 생성 금지`는 별도 문서에서 "raw evidence 복사 금지와 provenance 유지"로 재정의한다.

## 7. 다음 단계

1. 이 의사결정 기록을 검토한다.
2. `구현 전에 확정할 사항` 중 변경할 항목이 있으면 수정한다.
3. 결정이 확정되면 `docs/superpowers/plans`에 구현 계획서를 작성한다.
4. 구현 계획서는 테스트 우선으로 작성한다.
5. 구현은 `display_reason raw 노출 방지`, `content_id dedup`, `requested_count`, `section fallback`, `dislike filter` 순서로 진행한다.
