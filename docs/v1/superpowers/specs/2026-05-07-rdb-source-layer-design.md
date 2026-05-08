# RDB Source Layer Separation Design

## Goal

RIMAS RDB 확장 패치를 기존 서비스 계약을 깨지 않는 방식으로 반영하기 위해 Source Layer와 Runtime Contract Layer를 분리한다.

## Background

현재 프로젝트의 기존 DB 문서는 PostgreSQL 기준으로 다음 런타임 계약 테이블을 중심으로 정의되어 있다.

- `users`
- `ml_outputs`
- `music_catalog`
- `interaction_logs`
- 선택: `llm_call_logs`, `validation_logs`

별도 데이터셋 경로의 RDB 패치 설계는 Spotify/KKBOX 원천 데이터 적재를 위해 다음 테이블을 추가한다.

- `spotify_tracks`
- `spotify_audio_features`
- `spotify_lyrics`
- `spotify_emotions`
- `kkbox_user_features`
- `user_music_profiles`
- `interaction_logs_archive`

이 추가 테이블을 기존 런타임 계약과 같은 책임으로 취급하면 Service Layer가 원천 테이블에 직접 의존하게 되고, 기존 문서의 Repository/Service 경계를 위반할 수 있다. 따라서 추가 테이블은 Source Layer로 분리한다.

## Architecture

RDB는 두 계층으로 구분한다.

```text
Source Layer
  -> Spotify/KKBOX 원천 데이터, 전처리 결과, provenance 보존
  -> Runtime Service Flow의 직접 의존 대상이 아님

Runtime Contract Layer
  -> Service, RAG Mock, Agent Flow가 안정적으로 의존하는 앱 계약
  -> 기존 docs의 서비스 흐름과 JSON 계약을 유지
```

데이터 흐름은 다음을 따른다.

```text
Spotify/KKBOX raw data
  -> loader / transformer / validator
  -> Source Layer tables
  -> catalog/profile build process
  -> Runtime Contract tables
  -> Repository Layer
  -> Service Layer
  -> KAG/RAG/Agent/UI
```

## Source Layer

Source Layer는 원천 데이터와 전처리 산출물을 저장한다.

대상 테이블:

- `spotify_tracks`
- `spotify_audio_features`
- `spotify_lyrics`
- `spotify_emotions`
- `kkbox_user_features`
- `user_music_profiles`

책임:

- Spotify track 기반 음악 원천 정보 보존
- Spotify audio feature 보존
- lyrics/emotion normalize exact join 결과 보존
- KKBOX 사용자 feature 보존
- 사용자 취향 profile 후보 보존
- 원본 row는 가능한 경우 `raw_json`, `feature_json`, `profile_json`에 보존

금지:

- Service Layer에서 Source Layer 테이블을 직접 조회하지 않는다.
- UI에서 Source Layer 테이블을 직접 조회하지 않는다.
- Source Layer 적재 단계에서 추천 결정을 수행하지 않는다.
- `recommendation_category`를 과도하게 확정하지 않는다.
- fuzzy matching, random ID, UUID 기반 `content_id` 생성을 사용하지 않는다.

## Runtime Contract Layer

Runtime Contract Layer는 기존 서비스 흐름이 의존하는 안정된 테이블 계약이다.

대상 테이블:

- `users`
- `ml_outputs`
- `music_catalog`
- `interaction_logs`
- 선택: `llm_call_logs`
- 선택: `validation_logs`

책임:

- `users`: 런타임 사용자 식별 기준
- `ml_outputs`: 사용자 취향/행동 기반 ML 결과 계약
- `music_catalog`: RAG Mock이 조회 가능한 음악 후보 계약
- `interaction_logs`: 서비스 실행 결과 append-only 로그

유지 원칙:

- 기존 Service Flow는 Runtime Contract Layer를 기준으로 유지한다.
- RAG Mock은 기본적으로 `music_catalog`만 조회한다.
- LLM은 `RAG_STATE`에 없는 곡을 생성하지 않는다.
- Repository Layer만 SQL을 실행한다.
- SQL은 `app/repositories/query_constants.py`에 상수화한다.

## Repository Boundary

Repository는 두 책임으로 나눈다.

```text
Runtime Repository
  -> Service Layer가 호출 가능
  -> MlOutputRepository
  -> MusicCatalogRepository
  -> InteractionLogRepository

Source Repository
  -> loader, transformer, catalog build process에서만 사용
  -> SpotifyTrackRepository
  -> SpotifyAudioFeatureRepository
  -> SpotifyLyricsRepository
  -> SpotifyEmotionRepository
  -> KkboxUserFeatureRepository
  -> UserMusicProfileRepository
```

Service Layer는 Runtime Repository만 의존한다. Source Repository는 전처리/적재/빌드 계층의 내부 구현으로 제한한다.

## Transformation Rules

Spotify 데이터는 다음 규칙으로 Runtime Contract에 반영한다.

```text
spotify_tracks
+ spotify_audio_features
+ spotify_lyrics
+ spotify_emotions
  -> music_catalog
```

KKBOX 데이터는 다음 규칙으로 Runtime Contract에 반영한다.

```text
kkbox_user_features
+ user_music_profiles
  -> users
  -> ml_outputs
```

`music_catalog.content_id`는 deterministic 규칙을 따른다.

```text
content_id = "mc_" + track_id
```

금지:

- `track_id`가 없는 데이터를 임의 ID로 보정하지 않는다.
- normalize exact join 실패 데이터를 강제 적재하지 않는다.
- lyrics/emotion 미매칭 데이터를 사실처럼 병합하지 않는다.

## Schema Compatibility

기존 프로젝트 스키마와 vFinal 패치 설계 사이의 차이는 별도 마이그레이션 단계에서 명시적으로 다룬다.

주의가 필요한 항목:

- `users`에 `source_user_id`, `source_type` 추가
- `music_catalog`에 `track_id` 추가 및 `content_id` 길이 확장
- `ml_outputs` nullable placeholder 정책 적용 여부
- `interaction_logs`의 기존 컬럼 유지 여부
- `interaction_logs_archive` 도입 여부

기본 결정:

- `interaction_logs.primary_goal`, `intent_type`, `target_page`, `primary_section`은 기존 서비스 로그 계약이므로 유지한다.
- `ml_outputs` nullable 완화는 기존 Repository/Service 계약 영향 분석 후 별도 승인한다.
- `spotify_*`, `kkbox_*`, `user_music_profiles`는 Source Layer로 추가하되 Service Flow의 직접 의존 대상이 아니다.

## Testing And Verification

문서 반영 후 구현 단계에서는 다음 검증을 수행한다.

- PostgreSQL DDL 적용 가능 여부
- Source Layer FK 무결성
- `music_catalog.content_id = mc_{track_id}` 규칙
- duplicate `track_id` 없음
- unmatched report 생성 여부
- Runtime Repository 기존 테스트 통과
- Service Layer가 Source Repository를 직접 import하지 않는지 확인
- RAG Mock이 `music_catalog`에 존재하는 곡만 반환하는지 확인

## Non-Goals

이번 설계는 다음을 구현하지 않는다.

- KAG 구현
- RAG 구현
- Graph DB
- Vector DB
- Embedding 생성
- LLM 기반 추천 생성
- title/artist fuzzy matching
- KKBOX song_id와 Spotify track_id 직접 매핑

## Approval Summary

승인된 방향:

- 추가 Spotify/KKBOX 테이블은 Source Layer로 분리한다.
- 기존 앱 서비스 흐름은 Runtime Contract Layer를 기준으로 유지한다.
- Source Layer는 Service Layer의 직접 의존 대상이 아니다.
- Runtime Service Flow는 Repository Layer를 통해서만 DB에 접근한다.
