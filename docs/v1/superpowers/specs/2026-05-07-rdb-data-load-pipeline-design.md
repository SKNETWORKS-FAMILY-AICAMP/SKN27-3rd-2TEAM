# RDB Data Load Pipeline Design

## Goal

Source Layer 테이블에 Spotify/KKBOX 데이터를 적재할 수 있도록 수동 적재와 Docker 초기화 자동 적재를 모두 지원한다. 기본 운영 경로는 수동 적재이며, Docker 자동 적재는 새 PostgreSQL volume을 만들 때만 동작하는 선택 옵션으로 둔다.

## Background

현재 프로젝트는 PostgreSQL Docker 초기화에서 다음 파일만 실행한다.

```text
db/schema.sql
db/seed.sql
```

이전 단계에서 Source Layer 테이블은 스키마에 추가되었지만, 실제 데이터 적재 경로는 아직 연결되지 않았다. 외부 데이터셋 경로 `C:\dev\Project\dataset\database`에는 다음 적재 자산이 존재한다.

```text
sql/load_kkbox_seed.sql
sql/load_spotify_catalog.sql
data/load/*.csv
seed/*.csv
loaders/
scripts/
raw/
```

이번 설계는 외부 데이터셋 폴더의 개념을 현재 프로젝트에 연결하되, raw 대용량 파일을 프로젝트 repo에 직접 넣는 것을 목표로 하지 않는다.

## Scope

이번 파이프라인은 다음을 지원한다.

- 수동 적재 명령
- Docker 초기화 시 선택적 자동 적재
- 적재 전 파일 존재 검증
- 적재 후 count/FK/중복 검증
- 기존 Runtime Contract 보호

이번 파이프라인은 다음을 구현하지 않는다.

- KAG/RAG 구현
- Vector DB/Embedding 생성
- LLM 추천 생성
- fuzzy matching
- KKBOX song_id와 Spotify track_id 직접 매핑
- raw 대용량 데이터 파일의 git 포함

## Architecture

데이터 적재는 두 경로로 제공한다.

```text
Manual Load
  -> 개발자가 명령으로 load CSV 생성/확인
  -> psql load script 실행
  -> 검증 쿼리 실행

Optional Docker Init Load
  -> 새 PostgreSQL volume 생성 시에만 실행
  -> data/load 및 seed 파일이 있으면 적재
  -> 파일이 없으면 Source Layer 적재를 건너뛰고 schema/seed만 유지
```

Source Layer와 Runtime Contract Layer 경계는 유지한다.

```text
Source Layer
  -> spotify_tracks
  -> spotify_audio_features
  -> spotify_lyrics
  -> spotify_emotions
  -> kkbox_user_features
  -> user_music_profiles

Runtime Contract Layer
  -> users
  -> ml_outputs
  -> music_catalog
  -> interaction_logs
```

Service Layer는 Source Layer를 직접 조회하지 않는다. Source Layer 데이터는 loader/transformer/catalog build 과정을 거쳐 `music_catalog`, `ml_outputs`에 반영된 뒤 Runtime Repository를 통해 사용한다.

## File Layout

현재 프로젝트에는 다음 구조를 추가한다.

```text
db/
  load/
    load_kkbox_seed.sql
    load_spotify_catalog.sql
    verify_source_load.sql
  init/
    03-load-source-data.sh

data/
  load/
    .gitkeep

seed/
  .gitkeep
```

역할:

- `db/load/load_kkbox_seed.sql`: `seed/users.csv`, `seed/kkbox_user_features.csv`를 Source/Runtime 테이블에 적재한다.
- `db/load/load_spotify_catalog.sql`: `data/load/*_load.csv`를 Spotify Source 테이블과 `music_catalog`에 적재한다.
- `db/load/verify_source_load.sql`: 적재 결과 count, FK 누락, 중복 track_id를 검증한다.
- `db/init/03-load-source-data.sh`: Docker initdb 단계에서 파일이 있을 때만 load SQL을 실행한다.
- `data/load/`: 생성된 Spotify load CSV가 놓이는 위치다.
- `seed/`: 생성된 KKBOX seed CSV가 놓이는 위치다.

## Manual Load Flow

수동 적재는 기본 경로다.

```text
1. load CSV 준비
2. docker compose up -d db
3. schema 적용 상태 확인
4. KKBOX load SQL 실행
5. Spotify load SQL 실행
6. verify SQL 실행
```

명령 예시는 문서에 다음 형태로 제공한다.

```powershell
docker exec rimas_db psql -U rimas -d rimas -f /workspace/db/load/load_kkbox_seed.sql
docker exec rimas_db psql -U rimas -d rimas -f /workspace/db/load/load_spotify_catalog.sql
docker exec rimas_db psql -U rimas -d rimas -f /workspace/db/load/verify_source_load.sql
```

수동 명령은 `docker compose exec db ...` 형태를 사용한다. 현재 `docker-compose.yml`에는 명시적 `container_name`이 없으므로 고정 container name에 의존하지 않는다.

## Optional Docker Init Load Flow

Docker 자동 적재는 새 PostgreSQL volume에서만 동작한다. PostgreSQL 공식 entrypoint의 특성상 `/docker-entrypoint-initdb.d` 스크립트는 데이터 디렉터리가 비어 있을 때만 실행된다.

자동 적재는 다음 조건을 만족할 때만 실행한다.

```text
seed/users.csv 존재
seed/kkbox_user_features.csv 존재
data/load/spotify_tracks_load.csv 존재
data/load/spotify_audio_features_load.csv 존재
data/load/music_catalog_load.csv 존재
```

lyrics/emotion 파일은 선택적으로 취급한다. 파일이 없으면 해당 테이블 적재를 건너뛴다.

자동 적재 스크립트는 파일이 없을 때 실패하지 않고 메시지를 출력한 뒤 종료한다. 이 정책은 팀원이 raw/load 파일 없이 dev를 실행할 수 있게 하기 위한 것이다.

## Data File Policy

raw 대용량 파일은 현재 프로젝트 git에 포함하지 않는다.

`.gitignore` 정책:

```text
data/load/*
!data/load/.gitkeep
seed/*
!seed/.gitkeep
```

필요하면 아주 작은 fixture CSV만 `tests/fixtures` 아래에 둔다. 운영/개발 적재용 CSV는 로컬 생성물로 취급한다.

## Load Script Rules

적재 SQL은 `\copy`를 사용한다. 이유는 파일이 컨테이너 안에서 접근 가능한 경로에 마운트되고, PostgreSQL 서버 권한보다 psql client 권한으로 다루는 것이 개발 환경에서 단순하기 때문이다.

기본 경로는 컨테이너 내부 `/workspace`로 통일한다.

```text
/workspace/seed/users.csv
/workspace/seed/kkbox_user_features.csv
/workspace/data/load/spotify_tracks_load.csv
/workspace/data/load/spotify_audio_features_load.csv
/workspace/data/load/spotify_lyrics_load.csv
/workspace/data/load/spotify_emotions_load.csv
/workspace/data/load/music_catalog_load.csv
```

적재 순서:

```text
1. users
2. spotify_tracks
3. spotify_audio_features
4. spotify_lyrics
5. spotify_emotions
6. music_catalog
7. kkbox_user_features
8. user_music_profiles
```

`user_music_profiles`는 현재 외부 `load_kkbox_seed.sql`에 적재 규칙이 없으므로 이번 1차 구현의 load SQL 대상에서 제외한다. 테이블은 Source Layer 스키마로 유지한다.

## Verification

검증 SQL은 최소한 다음을 확인한다.

- 주요 테이블 count
- Spotify FK 누락
- 중복 `spotify_tracks.track_id`
- `music_catalog.content_id` 누락
- `music_catalog.track_id` 누락
- `music_catalog.content_id = 'mc_' || track_id` 규칙

검증 실패 기준은 SQL 결과로 명확히 드러나야 한다. 구현 단계에서는 테스트가 검증 SQL 안에 필요한 쿼리 이름과 조건이 포함되어 있는지 확인한다.

## Error Handling

수동 적재:

- 필수 CSV가 없으면 psql load 단계에서 실패한다.
- 실패 시 개발자가 파일 생성/경로 문제를 확인한다.
- README에 필수 파일 목록과 생성 순서를 명시한다.

Docker 자동 적재:

- 필수 CSV가 없으면 적재를 건너뛰고 DB schema/기본 seed만 유지한다.
- 일부 선택 CSV가 없으면 해당 선택 테이블만 건너뛴다.
- 새 volume에서만 실행된다는 점을 README에 명시한다.

## Documentation Updates

README에는 다음을 추가한다.

- 수동 적재 절차
- 자동 적재 조건
- 기존 volume에는 init script가 다시 실행되지 않는다는 주의
- 재초기화가 필요한 경우 `docker compose down -v`를 사용한다는 안내
- raw/load 파일은 git에 포함하지 않는다는 정책

DB 문서에는 Source Layer 적재 파일과 검증 SQL 위치를 추가한다.

## Testing Strategy

구현 단계에서는 실제 대용량 CSV를 테스트에 사용하지 않는다.

테스트는 다음을 검증한다.

- load SQL 파일 존재
- load SQL의 `\copy` 대상 테이블과 경로
- verify SQL의 필수 검증 쿼리
- Docker Compose가 init script와 load 디렉터리를 마운트하는지
- `.gitignore`가 대용량 생성 파일을 제외하는지
- README에 수동/자동 적재 주의사항이 포함되는지

## Approval Summary

승인된 방향:

- 수동 적재와 Docker 초기화 자동 적재를 둘 다 지원한다.
- 수동 적재를 기본 경로로 둔다.
- Docker 자동 적재는 새 volume에서 파일이 있을 때만 실행되는 선택 옵션으로 둔다.
- raw 대용량 데이터는 git에 포함하지 않는다.
- Source Layer와 Runtime Contract Layer 경계는 유지한다.
