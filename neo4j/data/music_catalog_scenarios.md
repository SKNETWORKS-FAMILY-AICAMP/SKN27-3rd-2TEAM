# music_catalog_scenarios.csv — 컬럼 및 시나리오 태그 설명

음원 추천·검색용으로 트랙별 **청취 맥락(컨텍스트)** 을 차원별로 라벨링한 CSV 파일입니다. Neo4j 등에 적재할 때 `track_id`(Spotify 트랙 ID와 동일한 형태)를 키로 사용할 수 있습니다.

---

## 파일 개요

| 항목 | 설명 |
|------|------|
| 행 단위 | 한 트랙(`track_id`)당 한 행 |
| 다중 값 | 같은 칸에 태그가 여러 개일 때 **세미콜론(`;`)** 으로 구분 (예: `time_morning;time_afternoon`) |
| 빈 값 | 해당 차원에 라벨이 없으면 빈 문자열 또는 생략에 해당하는 형태 |

---

## 컬럼 정의

| 컬럼명 | 타입 · 의미 | 비고 |
|--------|--------------|------|
| `track_id` | 문자열 · 트랙 식별자 | 외부 음원 DB(예: Spotify)의 트랙 ID |
| `dim_weather` | 시나리오 차원 · **날씨** 관련 태그 | 접두사 `weather_` |
| `dim_season` | **계절** | 접두사 `season_` |
| `dim_emotion` | **감정/무드**(음악적·청취 감정 쪽) | 접두사 `emotion_` |
| `dim_time_of_day` | **하루 중 시간대** | 접두사 `time_` · 다중 시간대 허용 |
| `dim_energy_level` | **에너지/템포 강도**에 대한 차원 | 접두사 `energy_level_` |
| `dim_ctx_commute` | **통근/이동**(출퇴근·운전 등) 컨텍스트 | 접두사 `commute_` |
| `dim_ctx_home` | **집 안 활동** 컨텍스트 | 접두사 `home_` |
| `dim_ctx_focus` | **몰입/업무·학습** 컨텍스트 | 접두사 `focus_` |
| `dim_ctx_exercise` | **운동** 컨텍스트 | 접두사 `exercise_` |
| `dim_ctx_social` | **사람들과 함께하는** 자리·관계 컨텍스트 | 접두사 `social_` |
| `dim_ctx_emotion_sit` | **감정적 상황/심리적 맥락**(연애 끝, 위로 등) | 접두사 `sit_`(situation) |
| `dim_ctx_travel` | **여행·이동 준비·이동 중** 등 | 접두사 `travel_` |
| `dim_ctx_special` | **카페·클럽·축제** 등 특수 장소·이벤트성 맥락 | 접두사 `special_` |
| `scenario_tags_all` | 해당 행에 등장하는 **모든 태그의 통합 문자열** | 세미콜론으로 연결된 **합집합** · 검색·전체 카운팅 편의용 |
| `scenario_tag_count` | `scenario_tags_all`에 포함된 태그 **개수**(정수) | 세미콜론으로 나뉜 토큰 수와 일치 |

`scenario_tags_all`은 차원별 열에 흩어진 값들을 하나로 모은 결과이므로, **그래프 모델에서 개별 차원별 엣지/속성을 만들 때는 `dim_*` 열을 우선** 참고하고, 빠른 전체 검색에는 `scenario_tags_all`을 쓸 수 있습니다.

---

## 태그 네이밍 규칙

- 형식: `{카테고리 접두사}_{구체값}` (스네이크 케이스)
- 카테고리 접두사는 위 `dim_*` 열과 1:1로 대응합니다(`energy_level_*` 예외적으로 두 단어 접두사).
- 동일 카테고리 내에서 여러 태그가 동시에 성립하면 한 셀에 `;`로 나열합니다.

---

## 오디오 피처 원천·분류 파이프라인

`music_catalog_scenarios.csv`는 **`music_catalog.csv`에 있는 트랙별 Spotify 오디오 피처**를 읽은 뒤, `neo4j/common/classified_catalog.py`가 규칙을 평가해 생성합니다. 규칙은 `neo4j/spotify_music_recommendation_guide.md`의 **권장 구간 표**와 맞도록 설계되었으며, **실제로 태그가 붙는 조건은 `classified_catalog.py`의 `predicate` 함수**가 단일 근거입니다(가이드 문구와 다른 경우 아래 표·코드를 우선합니다).

| 단계 | 설명 |
|------|------|
| 입력 | `music_catalog.csv`(행별 `track_id` + 오디오 수치 컬럼) |
| 분류기 | `classify_catalog()` → 각 행마다 `SCENARIO_RULES` 전부 평가 |
| 규칙 만족 | 한 태그에 대해 **명시된 모든 조건이 AND로 동시에 참**일 때만 해당 태그 부여 |
| 출력 | 본 문서의 `dim_*`, `scenario_tags_all`, `scenario_tag_count` |

결측이 있는 컬럼이 규칙에 필요하면 해당 규칙은 **실패**(그 태그 미부여)로 처리합니다.

### 사용하는 오디오 컬럼·스케일 (요약)

| 컬럼 | 의미 | 구현 시 유의 |
|------|------|--------------|
| `energy` | 활기·강도 | 0.0 ~ 1.0 |
| `valence` | 감정적 긍정성 | 0.0 ~ 1.0 |
| `danceability` | 댄스 적합도 | 0.0 ~ 1.0 |
| `tempo` | BPM | 구간 필터 시 **양끝 포함** (`60 ≤ tempo ≤ 90` 형태) |
| `acousticness` | 어쿠스틱 성향 | 0.0 ~ 1.0 |
| `instrumentalness` | 연주곡(보컬 적음) 성향 | 0.0 ~ 1.0 |
| `speechiness` | 말소리 비율 | 0.0 ~ 1.0 |
| `loudness` | dB 근사 | 예: ≤ -10, ≥ -6 |
| `liveness` | 라이브 느낌 | 0.0 ~ 1.0 |
| `mode` | 장조·단조 | CSV에 실수로 들어와도 코드에서 **`mode_bin`**: ≥ 0.5 → 장조 **1**, 그 외 단조 **0** |

### 추천·필터링 우선순위 (가이드 정리)

런타임에서 시나리오 외 **`music_catalog` 수치만으로 2차 필터**할 때는 가이드에서 제안하는 우선순위를 참고할 수 있습니다.

1. `energy` + `valence` → 전체 무드
2. `tempo` → 빠르기
3. `acousticness` + `instrumentalness` → 음색·가사/보컬 비중
4. `mode` + `danceability` → 세부 감성
5. 보조: `speechiness`(랩·토크 회피), `liveness`(라이브 감성), `loudness`(고강도 상황 미세 조정)

---

## 태그별 수치 필터 (`classified_catalog.py` 구현)

각 태그는 아래 조건을 **모두 만족**해야 CSV에 기록됩니다. 범위는 닫힌 구간 **이상·이하**로 이해하면 됩니다.

### 날씨 (`dim_weather`)

| 태그 | 오디오 조건 |
|------|-------------|
| `weather_sunny` | `valence` ≥ 0.6 · `energy` ≥ 0.5 · **장조**(mode_bin = **1**) |
| `weather_rain` | `valence` ≤ 0.4 · `acousticness` ≥ 0.5 · **단조**(0) · `tempo` 60 ~ 90 |
| `weather_snow` | `acousticness` ≥ 0.6 · `valence` 0.3 ~ 0.6 · `tempo` ≤ 80 |
| `weather_cloudy` | **단조** · `valence` 0.3 ~ 0.5 · `energy` 0.3 ~ 0.5 |

### 계절 (`dim_season`)

| 태그 | 오디오 조건 |
|------|-------------|
| `season_spring` | `valence` ≥ 0.6 · `energy` 0.4 ~ 0.7 · `acousticness` ≥ 0.4 · `tempo` 90 ~ 120 |
| `season_summer` | `energy` ≥ 0.7 · `danceability` ≥ 0.6 · `valence` ≥ 0.6 · `tempo` ≥ 120 |
| `season_autumn` | **단조** · `valence` 0.3 ~ 0.5 · `acousticness` ≥ 0.5 |
| `season_winter` | `acousticness` ≥ 0.5 · `valence` ≤ 0.4 · `energy` ≤ 0.4 |

### 감정 (`dim_emotion`)

| 태그 | 오디오 조건 | 비고 |
|------|-------------|------|
| `emotion_lonely` | **단조** · `valence` ≤ 0.3 · `acousticness` ≥ 0.6 | 가이드의 「외로움」 근거 |
| `emotion_melancholy` | `valence` ≤ 0.3 · **단조** · `energy` ≤ 0.4 · `tempo` ≤ 80 | 가이드 「우울함」 |
| `emotion_hyped` | `energy` ≥ 0.8 · `danceability` ≥ 0.7 · `valence` ≥ 0.7 · `tempo` ≥ 120 | 가이드 「신남」 |
| `emotion_thrill` | `valence` ≥ 0.6 · `energy` 0.5 ~ 0.7 · **장조** · `tempo` 100 ~ 130 | 가이드 「설렘」 표와 동일 로직(**태그 id는 thrill**) |

### 시간대 (`dim_time_of_day`)

| 태그 | 오디오 조건 |
|------|-------------|
| `time_morning` | `energy` 0.5 ~ 0.7 · `valence` ≥ 0.6 · `tempo` 100 ~ 120 · **장조** |
| `time_afternoon` | `energy` 0.5 ~ 0.8 · `valence` 0.5 ~ 0.8 |
| `time_evening` | `valence` 0.3 ~ 0.6 · `acousticness` ≥ 0.4 · `energy` ≤ 0.5 |
| `time_night` | `acousticness` ≥ 0.5 · `energy` ≤ 0.4 · `tempo` ≤ 90 |
| `time_dawn` | `instrumentalness` ≥ 0.5 · `energy` ≤ 0.3 · `loudness` ≤ -10 |

### 에너지 레벨 (`dim_energy_level`)

| 태그 | 오디오 조건 |
|------|-------------|
| `energy_level_calm` | `energy` ≤ 0.4 · `tempo` ≤ 90 · `acousticness` ≥ 0.5 · `loudness` ≤ -8 |
| `energy_level_moderate` | `energy` 0.4 ~ 0.7 · `tempo` 90 ~ 120 |
| `energy_level_hyped` | `energy` ≥ 0.7 · `danceability` ≥ 0.7 · `tempo` ≥ 120 |

### 통근 (`dim_ctx_commute`)

| 태그 | 오디오 조건 |
|------|-------------|
| `commute_to_work` | `energy` 0.5 ~ 0.7 · `valence` ≥ 0.5 · `tempo` 100 ~ 120 · **장조** |
| `commute_from_work` | `valence` 0.3 ~ 0.6 · `energy` ≤ 0.5 · `acousticness` ≥ 0.3 |
| `commute_public` | `instrumentalness` ≥ 0.4 · `energy` 0.3 ~ 0.6 · `speechiness` ≤ 0.1 |
| `commute_drive` | `energy` 0.6 ~ 0.8 · `tempo` 110 ~ 140 · `danceability` ≥ 0.6 · `valence` ≥ 0.5 |

### 집 (`dim_ctx_home`)

| 태그 | 오디오 조건 |
|------|-------------|
| `home_chores` | `energy` 0.5 ~ 0.7 · `danceability` ≥ 0.6 · `valence` ≥ 0.5 |
| `home_cooking` | `valence` ≥ 0.5 · `tempo` 100 ~ 130 · `danceability` 0.5 ~ 0.7 |
| `home_shower` | `energy` ≥ 0.6 · `valence` ≥ 0.6 |
| `home_rest` | `acousticness` ≥ 0.5 · `energy` ≤ 0.4 · `instrumentalness` ≥ 0.3 |
| `home_sleep` | `energy` ≤ 0.3 · `tempo` ≤ 70 · `acousticness` ≥ 0.6 · `loudness` ≤ -10 |

### 집중 (`dim_ctx_focus`)

| 태그 | 오디오 조건 |
|------|-------------|
| `focus_study` | `instrumentalness` ≥ 0.7 · `speechiness` ≤ 0.05 · `energy` 0.3 ~ 0.5 |
| `focus_office` | `instrumentalness` ≥ 0.6 · `energy` 0.4 ~ 0.6 · `tempo` 90 ~ 120 |
| `focus_deadline` | `energy` 0.6 ~ 0.8 · `tempo` ≥ 120 · `instrumentalness` ≥ 0.5 |

### 운동 (`dim_ctx_exercise`)

| 태그 | 오디오 조건 |
|------|-------------|
| `exercise_gym` | `energy` ≥ 0.8 · `tempo` ≥ 130 · `danceability` ≥ 0.7 · `loudness` ≥ -6 |
| `exercise_walk` | `valence` ≥ 0.5 · `energy` 0.4 ~ 0.6 · `tempo` 90 ~ 110 |
| `exercise_stretch` | `energy` ≤ 0.4 · `acousticness` ≥ 0.5 · `tempo` ≤ 80 |

### 소셜 (`dim_ctx_social`)

| 태그 | 오디오 조건 |
|------|-------------|
| `social_date` | `valence` ≥ 0.5 · `acousticness` ≥ 0.3 · **장조** · `energy` 0.4 ~ 0.6 |
| `social_friends` | `danceability` ≥ 0.6 · `energy` ≥ 0.6 · `valence` ≥ 0.6 |
| `social_celebration` | **장조** · `valence` ≥ 0.7 · `energy` ≥ 0.6 |
| `social_homeparty` | `danceability` ≥ 0.7 · `energy` ≥ 0.7 · `valence` ≥ 0.6 · `tempo` ≥ 110 |

### 감정 상황 (`dim_ctx_emotion_sit`)

| 태그 | 오디오 조건 |
|------|-------------|
| `sit_breakup` | `valence` ≤ 0.3 · **단조** · `acousticness` ≥ 0.4 · `energy` ≤ 0.4 |
| `sit_comfort` | `valence` 0.3 ~ 0.5 · `acousticness` ≥ 0.5 · `tempo` ≤ 90 |
| `sit_mood_lift` | **장조** · `valence` ≥ 0.6 · `energy` ≥ 0.6 |
| `sit_nostalgia` | `valence` 0.4 ~ 0.7 · `acousticness` ≥ 0.4 |

### 여행 (`dim_ctx_travel`)

| 태그 | 오디오 조건 |
|------|-------------|
| `travel_prep` | `valence` ≥ 0.6 · `energy` ≥ 0.6 · `danceability` ≥ 0.5 |
| `travel_transit` | `instrumentalness` ≥ 0.4 · `energy` 0.3 ~ 0.5 |
| `travel_on_trip` | `energy` 0.6 ~ 0.8 · `valence` ≥ 0.6 · `tempo` 110 ~ 130 |

### 특수 (`dim_ctx_special`)

| 태그 | 오디오 조건 |
|------|-------------|
| `special_cafe` | `acousticness` ≥ 0.5 · `energy` 0.2 ~ 0.5 · `instrumentalness` ≥ 0.4 · `tempo` 70 ~ 100 |
| `special_club` | `danceability` ≥ 0.8 · `energy` ≥ 0.8 · `tempo` ≥ 125 · `loudness` ≥ -5 |
| `special_festival` | `energy` ≥ 0.8 · `liveness` ≥ 0.5 · `danceability` ≥ 0.7 |
| `special_gaming` | `energy` 0.6 ~ 0.9 · `tempo` ≥ 120 · `instrumentalness` ≥ 0.5 |
| `special_dawn_mood` | `valence` ≤ 0.4 · `acousticness` ≥ 0.6 · **단조** · `energy` ≤ 0.3 |

---

## 카테고리별 태그 목록 및 해설

아래 목록은 본 데이터에 **실제로 등장하는** 모든 태그 값을 기준으로 정리하였습니다.

### 날씨 · `weather_*` (`dim_weather`)

| 태그 | 의미(데이터 내 역할) |
|------|------------------------|
| `weather_sunny` | 맑은 날 · 밝은 야외 느낌에 어울리는 트랙 |
| `weather_cloudy` | 흐린 날 |
| `weather_rain` | 비 오는 날 |
| `weather_snow` | 눈·겨울 날씨 느낌 |

### 계절 · `season_*` (`dim_season`)

| 태그 | 의미 |
|------|------|
| `season_spring` | 봄 |
| `season_summer` | 여름 |
| `season_autumn` | 가을 |
| `season_winter` | 겨울 |

### 감정/무드 · `emotion_*` (`dim_emotion`)

| 태그 | 의미 |
|------|------|
| `emotion_hyped` | 신남 · 들뜸 · 업템포 무드에 가까운 청취 감정 |
| `emotion_thrill` | 짜릿함 · 긴장감 있는 흥분 |
| `emotion_melancholy` | 우울·melancholic한 감성 |
| `emotion_lonely` | 외로움 · 고독과 어울리는 무드 |

### 시간대 · `time_*` (`dim_time_of_day`)

| 태그 | 의미 |
|------|------|
| `time_morning` | 아침 |
| `time_afternoon` | 오후 |
| `time_evening` | 저녁 |
| `time_night` | 밤 |
| `time_dawn` | 새벽 |

### 에너지 레벨 · `energy_level_*` (`dim_energy_level`)

| 태그 | 의미 |
|------|------|
| `energy_level_hyped` | 높은 에너지(적극적·클럽풍 등 강한 드라이브) |
| `energy_level_moderate` | 중간 강도 |
| `energy_level_calm` | 차분함 · 낮은 텐션 |

### 통근/이동 · `commute_*` (`dim_ctx_commute`)

| 태그 | 의미 |
|------|------|
| `commute_to_work` | 출근 중 |
| `commute_from_work` | 퇴근 중 |
| `commute_drive` | 운전(자가 이동) 위주 통근 |
| `commute_public` | 대중교통 이용 통근 등 |

### 집 활동 · `home_*` (`dim_ctx_home`)

| 태그 | 의미 |
|------|------|
| `home_cooking` | 요리 중 |
| `home_shower` | 샤워·목욕 |
| `home_chores` | 집안일 |
| `home_rest` | 휴식 |
| `home_sleep` | 잠들기 전·수면 무드 |

### 몰입/업무 · `focus_*` (`dim_ctx_focus`)

| 태그 | 의미 |
|------|------|
| `focus_study` | 공부 |
| `focus_office` | 사무 · 업무 |
| `focus_deadline` | 마감 등 집중이 필요한 압박 상황 |

### 운동 · `exercise_*` (`dim_ctx_exercise`)

| 태그 | 의미 |
|------|------|
| `exercise_gym` | 헬스·헬창 무드 등 체육관 운동 |
| `exercise_walk` | 산책·보행 |
| `exercise_stretch` | 스트레칭·가벼운 운동 |

### 소셜 · `social_*` (`dim_ctx_social`)

| 태그 | 의미 |
|------|------|
| `social_friends` | 친구들과 |
| `social_date` | 데이트·로맨틱한 둘이서 |
| `social_celebration` | 축하 · 파티 느낌 |
| `social_homeparty` | 홈파티 |

### 감정적 상황 · `sit_*` (`dim_ctx_emotion_sit`)

| 태그 | 의미 |
|------|------|
| `sit_mood_lift` | 기분 전환을 원할 때 |
| `sit_breakup` | 이별 |
| `sit_comfort` | 위로가 필요할 때 |
| `sit_nostalgia` | 그리움·향수 |

### 여행/이동 · `travel_*` (`dim_ctx_travel`)

| 태그 | 의미 |
|------|------|
| `travel_prep` | 여행 준비 단계 · 설렘 |
| `travel_on_trip` | 여행 중 현지 |
| `travel_transit` | 공항·기차 등 이동 구간 자체 |

### 특수 장소·이벤트 · `special_*` (`dim_ctx_special`)

| 태그 | 의미 |
|------|------|
| `special_club` | 클럽·야간 클럽 씬 |
| `special_cafe` | 카페 분위기 |
| `special_festival` | 축제 · 페스티벌 |
| `special_gaming` | 게임 플레이 중 |
| `special_dawn_mood` | 새벽 감성·무드 등, `time_dawn`(시간대)과 병행 가능한 **특수 분위기** 라벨 |

---

## 활용 시 참고

1. **`scenario_tag_count`가 `0`** 인 행은 어떠한 시나리오 태그도 없는 트랙입니다.
2. 그래프 설계 예: 노드 `(Track)`에 속성으로 태그 배열을 두거나, `(Tag)` 노드와 `HAS_SCENARIO` 같은 관계로 풀 수 있습니다.
3. 동일 접두사(같은 `dim_*` 열) 내 다중값은 논리적 **AND**가 아니라 “이 트랙은 이 맥락들 각각과도 어울린다”는 **후보 태그 집합**으로 해석하는 것이 자연스럽습니다(추천 로직에서는 OR 또는 가중치로 처리).
4. 태그를 바꿀 계획이면 **`classified_catalog.py`의 임계값을 수정한 뒤** `music_catalog_scenarios.csv`를 다시 생성해야 Neo4j 쪽 시나리오와 수치 규칙이 일치합니다.

---

*본 문서는 `music_catalog_scenarios.csv` 내 실제 등장 태그 id를 기준으로 서술해 두었으며, **수치 임계·구간은 `neo4j/common/classified_catalog.py`**와 동일합니다. 시나리오 설계 의도와 서술은 `neo4j/spotify_music_recommendation_guide.md`를 참고했습니다. 데이터·규칙이 바뀌면 두 파일과 스크립트를 함께 맞추면 됩니다.*
