# music_catalog_scenarios.csv — 컬럼 및 분류 라벨 설명

음원 추천·검색용으로 트랙별 **청취 맥락**을 카테고리별 **라벨 열**에 적어 둔 CSV입니다. Neo4j 적재 시 `track_id`(Spotify 등과 동일한 문자열)를 키로 씁니다.

---

## 파일 개요

| 항목 | 설명 |
|------|------|
| 행 단위 | 한 트랙(`track_id`)당 한 행 |
| 다중 값 | 같은 칸에 라벨이 여러 개일 때 **세미콜론(`;`)** 으로 구분 (예: `morning;afternoon`, `energy_hyped;hyped`) |
| 빈 값 | 해당 **카테고리 라벨 열**에 부여된 태그가 없으면 빈 문자열 |

---

## Neo4j 그래프 (요약)

`neo4j/common/utils.py`의 `import_music_catalog_labels()`는 각 CSV 열마다 **값 노드**를 만들고 `MusicCatalog`와 연결합니다.

- 노드 라벨·관계 타입은 `neo4j/common/constant.py`의 `LABEL_CATEGORY_COLUMNS` / `LABEL_CATEGORY_TO_NODE_AND_REL` 과 동일합니다.
- 예: `weather` 열 값 `sunny` → 노드 라벨 `LabelWeather`(속성 `name`·`tag_id`), 관계 `(MusicCatalog)-[:HAS_LABEL_WEATHER]->(LabelWeather)`).

---

## 컬럼 정의 (`classified_catalog.CATEGORY_PRIORITY` 와 동일 순서)

CSV 열 이름은 분류 코드의 **카테고리 키**와 같습니다.

| 컬럼명 | 의미 | Neo4j 예시 노드 라벨 / 관계 |
|--------|------|------------------------------|
| `track_id` | 트랙 식별자 | `MusicCatalog` 매칭 키 |
| `emotion` | 감정·에너지 톤(차분함·신남·보통 등) | `LabelEmotion` · `HAS_LABEL_EMOTION` |
| `emotion_situation` | 감정적 상황(이별·위로 등) | `LabelEmotionSituation` · `HAS_LABEL_EMOTION_SIT` |
| `time` | 하루 중 시간대 | `LabelTime` · `HAS_LABEL_TIME` |
| `focus` | 몰입·업무·학습 맥락 | `LabelFocus` · `HAS_LABEL_FOCUS` |
| `exercise` | 운동 맥락 | `LabelExercise` · `HAS_LABEL_EXERCISE` |
| `home` | 집 안 활동 | `LabelHome` · `HAS_LABEL_HOME` |
| `commute` | 통근·이동 방식 | `LabelCommute` · `HAS_LABEL_COMMUTE` |
| `special` | 카페·클럽·페스티벌·게임·새벽 감성·**여행** 등 | `LabelSpecial` · `HAS_LABEL_SPECIAL` |
| `weather` | 날씨 느낌 | `LabelWeather` · `HAS_LABEL_WEATHER` |
| `season` | 계절 | `LabelSeason` · `HAS_LABEL_SEASON` |

**참고:** `build_music_catalog_labels_df()`가 만드는 CSV에는 `scenario_tags_all` / `scenario_tag_count` 열은 **포함되지 않습니다**. 전체 문자열 파생이 필요하면 파이프라인에서 따로 만들면 됩니다.

---

## 라벨(태그) 값 규약

- 셀에 들어가는 문자열은 `neo4j/common/classified_catalog.py`의 `CONDITIONS`에 정의된 **영문 식별자**입니다(카테고리마다 접두사를 붙이지 않음).
- 동일 카테고리 안에서 여러 라벨이 성립하면 `;`로 나열합니다.
- 카테고리마다 허용 태그는 아래 「태그별 수치 필터」와 `CONDITIONS`가 단일 근거입니다.

---

## 오디오 피처 원천·분류 파이프라인

| 단계 | 설명 |
|------|------|
| 입력 | `music_catalog.csv`(`track_id` + Spotify 오디오 피처 컬럼) |
| 분류기 | `build_music_catalog_labels_df()` → 각 행·각 카테고리에 대해 `CONDITIONS[category]` 전 태그를 평가 |
| 규칙 만족 | 한 태그에 대해 **명시된 모든 조건이 AND로 동시에 참**일 때만 해당 라벨 부여 |
| 출력 | 위 표의 카테고리 열 전부와 `track_id`(현재 `build_music_catalog_labels_df` 기준) |

결측 피처가 조건에서 필요하면 그 태그는 부여되지 않습니다.

### 사용하는 오디오 컬럼·스케일 (요약)

| 컬럼 | 의미 | 구현 시 유의 |
|------|------|--------------|
| `energy` | 활기·강도 | 0.0 ~ 1.0 |
| `valence` | 감정적 긍정성 | 0.0 ~ 1.0 |
| `danceability` | 댄스 적합도 | 0.0 ~ 1.0 |
| `tempo` | BPM | 구간 필터 시 **양끝 포함** |
| `acousticness` | 어쿠스틱 성향 | 0.0 ~ 1.0 |
| `instrumentalness` | 연주곡 성향 | 0.0 ~ 1.0 |
| `speechiness` | 말소리 비율 | 0.0 ~ 1.0 |
| `loudness` | dB 근사 | 상·하한 병행 가능 |
| `liveness` | 라이브 느낌 | 0.0 ~ 1.0 |
| `mode` | 장조·단조 | 규칙의 `_mode`는 `mode≥0.5` → 장조 **1**, 그 외 **0** 과 비교합니다 |

가이드 문서는 `neo4j/spotify_music_recommendation_guide.md`를 참고하되, 수치 테이블은 항상 `classified_catalog.py`의 `CONDITIONS`와 맞춥니다.

---

## 태그별 수치 필터 (`CONDITIONS`)

각 태그는 아래를 **모두 만족**해야 CSV 해당 열에 기록됩니다. `_mode`(0)·(1)·(1) 등은 해당 모드값과 일치할 때 참입니다.

### `emotion` 열

| 태그 | 조건 요약 |
|------|-----------|
| `lonely` | `valence` ≤ 0.3 · `acousticness` ≥ 0.6 · 단조 `_mode`(0) |
| `melancholy` | `valence` ≤ 0.3 · `energy` ≤ 0.4 · `tempo` ≤ 80 · 단조 |
| `hyped` | `energy` ≥ 0.8 · `danceability` ≥ 0.7 · `valence` ≥ 0.7 · `tempo` ≥ 120 |
| `thrill` | `valence` ≥ 0.6 · `energy` 0.5 ~ 0.7 · `tempo` 100 ~ 130 · 장조 `_mode`(1) |
| `calm` | `energy` ≤ 0.4 · `tempo` ≤ 90 · `acousticness` ≥ 0.5 · `loudness` ≤ -8 |
| `moderate` | `energy` 0.4 ~ 0.7 · `tempo` 90 ~ 120 |
| `energy_hyped` | `energy` ≥ 0.7 · `danceability` ≥ 0.7 · `tempo` ≥ 120 |

### `emotion_situation` 열

| 태그 | 조건 요약 |
|------|-----------|
| `breakup` | `valence` ≤ 0.3 · `acousticness` ≥ 0.4 · `energy` ≤ 0.4 · 단조 |
| `comfort` | `valence` 0.3 ~ 0.5 · `acousticness` ≥ 0.5 · `tempo` ≤ 90 |
| `mood_lift` | `valence` ≥ 0.6 · `energy` ≥ 0.6 · 장조 |
| `nostalgia` | `valence` 0.4 ~ 0.7 · `acousticness` ≥ 0.4 |

### `time` 열

| 태그 | 조건 요약 |
|------|-----------|
| `morning` | `energy` 0.5 ~ 0.7 · `valence` ≥ 0.6 · `tempo` 100 ~ 120 · 장조 |
| `afternoon` | `energy` 0.5 ~ 0.8 · `valence` 0.5 ~ 0.8 |
| `evening` | `valence` 0.3 ~ 0.6 · `acousticness` ≥ 0.4 · `energy` ≤ 0.5 |
| `night` | `acousticness` ≥ 0.5 · `energy` ≤ 0.4 · `tempo` ≤ 90 |
| `dawn` | `instrumentalness` ≥ 0.5 · `energy` ≤ 0.3 · `loudness` ≤ -10 |

### `focus` 열

| 태그 | 조건 요약 |
|------|-----------|
| `study` | `instrumentalness` ≥ 0.7 · `speechiness` ≤ 0.05 · `energy` 0.3 ~ 0.5 |
| `office` | `instrumentalness` ≥ 0.6 · `energy` 0.4 ~ 0.6 · `tempo` 90 ~ 120 |
| `deadline` | `energy` 0.6 ~ 0.8 · `tempo` ≥ 120 · `instrumentalness` ≥ 0.5 |

### `exercise` 열

| 태그 | 조건 요약 |
|------|-----------|
| `gym` | `energy` ≥ 0.8 · `tempo` ≥ 130 · `danceability` ≥ 0.7 · `loudness` ≥ -6 |
| `walk` | `valence` ≥ 0.5 · `energy` 0.4 ~ 0.6 · `tempo` 90 ~ 110 |
| `stretch` | `energy` ≤ 0.4 · `acousticness` ≥ 0.5 · `tempo` ≤ 80 |

### `home` 열

| 태그 | 조건 요약 |
|------|-----------|
| `chores` | `energy` 0.5 ~ 0.7 · `danceability` ≥ 0.6 · `valence` ≥ 0.5 |
| `cooking` | `valence` ≥ 0.5 · `tempo` 100 ~ 130 · `danceability` 0.5 ~ 0.7 |
| `shower` | `energy` ≥ 0.6 · `valence` ≥ 0.6 |
| `rest` | `acousticness` ≥ 0.5 · `energy` ≤ 0.4 · `instrumentalness` ≥ 0.3 |
| `sleep` | `energy` ≤ 0.3 · `tempo` ≤ 70 · `acousticness` ≥ 0.6 · `loudness` ≤ -10 |

### `commute` 열

| 태그 | 조건 요약 |
|------|-----------|
| `to_work` | `energy` 0.5 ~ 0.7 · `valence` ≥ 0.5 · `tempo` 100 ~ 120 · 장조 |
| `from_work` | `valence` 0.3 ~ 0.6 · `energy` ≤ 0.5 · `acousticness` ≥ 0.3 |
| `public` | `instrumentalness` ≥ 0.4 · `energy` 0.3 ~ 0.6 · `speechiness` ≤ 0.1 |
| `drive` | `energy` 0.6 ~ 0.8 · `tempo` 110 ~ 140 · `danceability` ≥ 0.6 · `valence` ≥ 0.5 |

### `special` 열 (여행 `travel` 포함)

| 태그 | 조건 요약 |
|------|-----------|
| `cafe` | `acousticness` ≥ 0.5 · `energy` 0.2 ~ 0.5 · `instrumentalness` ≥ 0.4 · `tempo` 70 ~ 100 |
| `club` | `danceability` ≥ 0.8 · `energy` ≥ 0.8 · `tempo` ≥ 125 · `loudness` ≥ -5 |
| `festival` | `energy` ≥ 0.8 · `liveness` ≥ 0.5 · `danceability` ≥ 0.7 |
| `gaming` | `energy` 0.6 ~ 0.9 · `tempo` ≥ 120 · `instrumentalness` ≥ 0.5 |
| `dawn_mood` | `valence` ≤ 0.4 · `acousticness` ≥ 0.6 · `energy` ≤ 0.3 · 단조 |
| `travel` | `valence` ≥ 0.6 · `energy` ≥ 0.6 · `danceability` ≥ 0.5 |

### `weather` 열

| 태그 | 조건 요약 |
|------|-----------|
| `sunny` | `valence` ≥ 0.6 · `energy` ≥ 0.6 · `danceability` ≥ 0.5 |
| `rain` | `valence` ≤ 0.4 · `acousticness` ≥ 0.6 · `energy` ≤ 0.5 · 단조 |
| `snow` | `acousticness` ≥ 0.6 · `energy` ≤ 0.4 · `valence` 0.2 ~ 0.5 |
| `cloudy` | `valence` 0.3 ~ 0.6 · `energy` 0.3 ~ 0.6 · `acousticness` ≥ 0.4 |

### `season` 열

| 태그 | 조건 요약 |
|------|-----------|
| `spring` | `valence` ≥ 0.6 · `energy` 0.4 ~ 0.7 · `acousticness` ≥ 0.4 · `tempo` 90 ~ 120 |
| `summer` | `energy` ≥ 0.7 · `danceability` ≥ 0.6 · `valence` ≥ 0.6 · `tempo` ≥ 120 |
| `autumn` | `valence` 0.3 ~ 0.5 · `acousticness` ≥ 0.5 · 단조 |
| `winter` | `acousticness` ≥ 0.5 · `valence` ≤ 0.4 · `energy` ≤ 0.4 |

---

## 한글 키워드 매핑 (에이전트·UI용 참고)

`classified_catalog.py`의 `_ALIAS`: 사용자가 한글 키워드를 넣으면 위 영문 태그 키로 변환 후 `CONDITIONS`를 조회합니다. 자세한 키 목록은 소스 파일의 `_ALIAS`를 참고하세요.

---

## 활용 시 참고

1. 한 행에서 **어떤 카테고리 열도 비어 있지 않을 필요는 없습니다**(오디오가 조건과 맞지 않으면 빈 문자열).
2. **같은 카테고리 열 안**의 세미콜론 구분 값들은 각각 그래프 상 별도 연결 가능한 **후보 라벨 집합**으로 두는 설계가 일반적입니다(추천 로직에서 OR·가중치 등으로 소비).
3. 규칙이나 라벨을 바꿀 계획이면 **`classified_catalog.py`**를 수정한 뒤 `music_catalog_scenarios.csv`를 다시 생성하고, Neo4j에 `import_music_catalog_labels()`로 재적재합니다.

---

*본 문서는 현재 분류 코드(`neo4j/common/classified_catalog.py`) 및 Neo4j 적재 스키마(`neo4j/common/constant.py`)와 맞도록 정리하였습니다.*
