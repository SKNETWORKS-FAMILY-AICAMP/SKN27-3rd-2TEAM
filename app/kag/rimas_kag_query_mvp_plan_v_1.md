# RIMAS KAG Query MVP Plan v1

## 목적

본 문서는 RIMAS 프로젝트의 1차 MVP 단계에서 사용할 KAG 기반 검색/추천 Query Type과 Cypher Query를 정의한다.

범위:
- Neo4j 기본 Cypher 기반
- Graph Data Science(GDS) 미사용
- KAG 단독 검색 및 추천
- RAG 미포함
- Tool 기반 Query 호출 구조

---

# 1. 전체 Query 구조

```text
QUERY_TYPES
├─ SEARCH
│  ├─ MUSIC_BASIC_INFO_LOOKUP
│  ├─ MUSIC_RELATION_INFO_LOOKUP
│  ├─ MUSIC_CONDITION_SEARCH
│  ├─ SIMILAR_MUSIC_LOOKUP
│  ├─ MUSIC_STAT_LOOKUP
│  ├─ CONNECTED_NODE_MUSIC_LOOKUP
│  ├─ MUSIC_COMMON_FEATURE_LOOKUP
│  ├─ MUSIC_PATH_LOOKUP
│  ├─ ARTIST_MUSIC_LOOKUP
│  ├─ CATEGORY_TOP_MUSIC_LOOKUP
│  ├─ TEMPORAL_MUSIC_LOOKUP
│  ├─ COMPOSITE_CONDITION_SEARCH
│  ├─ HIGH_CONNECTION_MUSIC_LOOKUP
│  └─ RELATION_TYPE_LOOKUP
│
└─ RECOMMENDATION
   ├─ GENRE_BASED_RECOMMENDATION
   ├─ MOOD_BASED_RECOMMENDATION
   ├─ SITUATION_BASED_RECOMMENDATION
   ├─ WEATHER_BASED_RECOMMENDATION
   ├─ SIMILAR_SONG_RECOMMENDATION
   ├─ POPULARITY_BASED_RECOMMENDATION
   ├─ DIVERSITY_RECOMMENDATION
   └─ HYBRID_CONTEXT_RECOMMENDATION
```

---

# 2. 공통 Tool 호출 구조

```python
result = tool_function(**params)
```

LLM/Agent 역할:
- 사용자 질문 분석
- intent_class 분류
- query_type 결정
- Tool 선택
- parameter 추출

Tool 역할:
- 고정 Cypher 실행
- 결과 반환
- 결과 후처리

금지:
- Agent가 Cypher 직접 생성
- LLM이 DB 구조 수정
- 존재하지 않는 추천 생성

---

# 3. 공통 응답 JSON 구조

```json
{
  "status": "success | partial_match | empty_result | error",
  "query_class": "SEARCH | RECOMMENDATION",
  "query_type": "MUSIC_BASIC_INFO_LOOKUP",
  "input_params": {},
  "results": [],
  "matched_count": 0,
  "message": null
}
```

---

# 4. SEARCH Query Types

---

## Q_SEARCH_001 / MUSIC_BASIC_INFO_LOOKUP

### 목적
특정 음악명의 직접 속성 조회

### Tool

```python
lookup_music_basic_info(keyword: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE toLower(m.track_name) CONTAINS toLower($keyword)
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_album_release_date AS release_date,
  m.playlist_genre AS genre,
  m.playlist_subgenre AS subgenre,
  m.duration_ms AS duration_ms,
  m.track_popularity AS popularity
ORDER BY m.track_popularity DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- Ditto 정보 알려줘
- Hype Boy 가수 누구야?
- Shape of You 앨범명이 뭐야?
- Attention 발매일 알려줘
- 이 노래 장르가 뭐야?

---

## Q_SEARCH_002 / MUSIC_RELATION_INFO_LOOKUP

### 목적
특정 음악과 연결된 노드 및 엣지 조회

### Tool

```python
lookup_music_relation_info(
    keyword: str,
    relation_filter: str | None = None,
    node_label_filter: str | None = None,
    limit: int = 50,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[r]-(n)
WHERE toLower(m.track_name) CONTAINS toLower($keyword)
  AND ($relation_filter IS NULL OR type(r) = $relation_filter)
  AND ($node_label_filter IS NULL OR $node_label_filter IN labels(n))
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  type(r) AS relation_type,
  labels(n) AS connected_node_labels,
  properties(n) AS connected_node_properties
LIMIT coalesce($limit, 50)
```

### 예상 질문
- Ditto랑 연결된 정보 보여줘
- 이 노래는 어떤 날씨랑 연결돼?
- Hype Boy랑 연결된 감정이 있어?
- Attention은 어떤 상황에 어울려?

---

## Q_SEARCH_003 / MUSIC_CONDITION_SEARCH

### 목적
조건 기반 음악 검색

### Tool

```python
search_music_by_conditions(
    genre=None,
    subgenre=None,
    artist=None,
    release_year=None,
    limit=20,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE
  ($genre IS NULL OR toLower(m.playlist_genre) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.playlist_subgenre) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.track_artist) CONTAINS toLower($artist))
  AND ($release_year IS NULL OR toString(m.track_album_release_date) STARTS WITH toString($release_year))
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_album_release_date AS release_date,
  m.playlist_genre AS genre,
  m.playlist_subgenre AS subgenre,
  m.track_popularity AS popularity
ORDER BY m.track_popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- pop 장르 음악 찾아줘
- rock 노래 보여줘
- 2019년에 나온 노래 찾아줘
- Taylor Swift 노래 검색해줘
- 힙합 장르 중 인기 있는 곡 보여줘

---

## Q_SEARCH_004 / SIMILAR_MUSIC_LOOKUP

### 목적
특정 음악과 공통 연결 요소가 있는 음악 검색

### Tool

```python
lookup_similar_music(keyword: str, limit: int = 20)
```

### Cypher

```cypher
MATCH (base:MusicCatalog)-[]-(feature)<-[]-(other:MusicCatalog)
WHERE toLower(base.track_name) CONTAINS toLower($keyword)
  AND base.content_id <> other.content_id
WITH other, count(DISTINCT feature) AS shared_feature_count
RETURN
  other.content_id AS content_id,
  other.track_name AS track_name,
  other.track_artist AS track_artist,
  shared_feature_count,
  other.track_popularity AS popularity
ORDER BY shared_feature_count DESC, popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- Ditto랑 비슷한 노래 찾아줘
- Hype Boy랑 비슷한 곡 보여줘
- 이 노래랑 분위기 비슷한 음악 있어?
- Attention 같은 느낌의 노래 찾아줘
- Shape of You랑 연결 요소가 비슷한 곡 보여줘

---

## Q_SEARCH_005 / MUSIC_STAT_LOOKUP

### 목적
장르/아티스트/연도 집계 조회

### Tool

```python
lookup_music_stat(stat_type: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
RETURN
  m.playlist_genre AS group_key,
  count(*) AS music_count
ORDER BY music_count DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 곡 수가 가장 많은 장르가 뭐야?
- 가장 많이 등장하는 장르 보여줘
- 데이터에 어떤 장르가 많아?
- 아티스트별 곡 수 보여줘
- 장르별 음악 개수 알려줘

---

## Q_SEARCH_006 / CONNECTED_NODE_MUSIC_LOOKUP

### 목적
특정 연결 노드 기준 음악 역조회

### Tool

```python
lookup_music_by_connected_node(
    node_value: str,
    node_label_filter: str | None = None,
    relation_filter: str | None = None,
    limit: int = 20,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[r]-(n)
WHERE
  ($node_label_filter IS NULL OR $node_label_filter IN labels(n))
  AND ($relation_filter IS NULL OR type(r) = $relation_filter)
  AND any(k IN keys(n) WHERE toLower(toString(n[k])) CONTAINS toLower($node_value))
RETURN DISTINCT
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  labels(n) AS matched_node_labels,
  properties(n) AS matched_node_properties
LIMIT coalesce($limit, 20)
```

### 예상 질문
- 비 오는 날과 연결된 음악 보여줘
- 운동할 때 듣기 좋은 음악 찾아줘
- sad랑 연결된 노래 있어?
- 밤에 어울리는 음악 보여줘
- 집중할 때 연결된 곡 찾아줘

---

## Q_SEARCH_007 / MUSIC_COMMON_FEATURE_LOOKUP

### 목적
두 음악의 공통 연결 요소 조회

### Tool

```python
lookup_music_common_features(
    music1: str,
    music2: str,
    limit: int = 20,
)
```

### Cypher

```cypher
MATCH (m1:MusicCatalog)-[]-(n)-[]-(m2:MusicCatalog)
WHERE toLower(m1.track_name) CONTAINS toLower($music1)
  AND toLower(m2.track_name) CONTAINS toLower($music2)
  AND m1.content_id <> m2.content_id
RETURN DISTINCT
  labels(n) AS common_node_labels,
  properties(n) AS common_node_properties
LIMIT coalesce($limit, 20)
```

### 예상 질문
- Ditto랑 Hype Boy 공통점 뭐야?
- Attention이랑 OMG가 공유하는 정보 있어?
- 두 곡의 공통 장르 알려줘
- Shape of You랑 비슷하게 연결된 요소가 뭐야?
- 이 두 노래가 같이 묶이는 이유가 있어?

---

## Q_SEARCH_008 / MUSIC_PATH_LOOKUP

### 목적
특정 음악의 그래프 경로 탐색

### Tool

```python
lookup_music_paths(
    keyword: str,
    target_label: str | None = None,
    max_depth: int = 3,
    limit: int = 10,
)
```

### Cypher

```cypher
MATCH p=(m:MusicCatalog)-[*1..3]-(n)
WHERE toLower(m.track_name) CONTAINS toLower($keyword)
  AND ($target_label IS NULL OR $target_label IN labels(n))
RETURN p
LIMIT coalesce($limit, 10)
```

### 예상 질문
- Ditto에서 연결 경로 보여줘
- 이 노래가 어떤 노드를 통해 추천되는지 보여줘
- Hype Boy의 그래프 연결 구조 보여줘
- 이 곡에서 감정 노드까지 가는 경로 보여줘
- Attention이 어떤 장르와 상황으로 연결되는지 보여줘

---

## Q_SEARCH_009 / ARTIST_MUSIC_LOOKUP

### 목적
특정 아티스트 기준 음악 조회

### Tool

```python
lookup_artist_music(artist: str, limit: int = 30)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE toLower(m.track_artist) CONTAINS toLower($artist)
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_name AS album_name,
  m.track_popularity AS popularity
ORDER BY popularity DESC
LIMIT coalesce($limit, 30)
```

### 예상 질문
- 아이유 노래 보여줘
- NewJeans 곡 목록 보여줘
- Taylor Swift 음악 찾아줘
- Ed Sheeran 노래 뭐 있어?
- BTS 곡 검색해줘

---

## Q_SEARCH_010 / CATEGORY_TOP_MUSIC_LOOKUP

### 목적
카테고리 내부 인기곡 조회

### Tool

```python
lookup_category_top_music(
    category_type: str,
    category_value: str,
    limit: int = 20,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE
  ($category_type = "genre" AND toLower(m.playlist_genre) = toLower($category_value))
  OR ($category_type = "subgenre" AND toLower(m.playlist_subgenre) = toLower($category_value))
  OR ($category_type = "artist" AND toLower(m.track_artist) CONTAINS toLower($category_value))
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_popularity AS popularity
ORDER BY popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- pop에서 인기 많은 노래 보여줘
- rock 장르 인기곡 알려줘
- 힙합 중 유명한 곡 찾아줘
- Taylor Swift 노래 중 인기곡 보여줘
- subgenre 기준으로 인기곡 찾아줘

---

## Q_SEARCH_011 / TEMPORAL_MUSIC_LOOKUP

### 목적
연도/기간 기준 음악 조회

### Tool

```python
lookup_temporal_music(
    year=None,
    start_year=None,
    end_year=None,
    limit=20,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WITH m, toInteger(left(toString(m.track_album_release_date), 4)) AS release_year
WHERE
  ($year IS NOT NULL AND release_year = $year)
  OR ($year IS NULL AND $start_year IS NOT NULL AND $end_year IS NOT NULL
      AND release_year >= $start_year AND release_year <= $end_year)
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.track_album_release_date AS release_date,
  m.track_popularity AS popularity
ORDER BY popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- 2018년에 나온 노래 보여줘
- 2020년 음악 찾아줘
- 2019년 pop 음악 있어?
- 최근 발매된 곡 보여줘
- 2015년부터 2020년 사이 노래 찾아줘

---

## Q_SEARCH_012 / COMPOSITE_CONDITION_SEARCH

### 목적
복합 조건 기반 음악 검색

### Tool

```python
search_music_by_composite_conditions(
    genre=None,
    mood=None,
    situation=None,
    weather=None,
    limit=20,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
OPTIONAL MATCH (m)-[:HAS_GENRE]-(g:Genre)
OPTIONAL MATCH (m)-[:HAS_LABEL_EMOTION]-(emo:LabelEmotion)
OPTIONAL MATCH (m)-[:HAS_LABEL_EXERCISE|HAS_LABEL_COMMUTE|HAS_LABEL_HOME|HAS_LABEL_FOCUS|HAS_LABEL_SPECIAL|HAS_LABEL_TIME|HAS_LABEL_SEASON|HAS_LABEL_EMOTION_SIT]-(s)
OPTIONAL MATCH (m)-[:HAS_LABEL_WEATHER]-(w:LabelWeather)
WITH m,
  max(CASE WHEN $genre IS NOT NULL AND toLower(g.genre) = toLower($genre) THEN 1 ELSE 0 END) AS genre_match,
  max(CASE WHEN $mood IS NOT NULL AND toLower(emo.name) CONTAINS toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.name) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.name) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m, genre_match + mood_match + situation_match + weather_match AS matched_count
WHERE matched_count > 0
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  matched_count,
  coalesce(m.track_popularity, 0) AS popularity
ORDER BY matched_count DESC, popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- 비 오는 날 듣기 좋은 잔잔한 pop 음악 찾아줘
- 운동할 때 듣는 신나는 힙합 보여줘
- 밤에 듣기 좋은 감성적인 노래 찾아줘
- 기분 좋을 때 들을 dance 음악 있어?
- 집중할 때 어울리는 조용한 음악 찾아줘

---

## Q_SEARCH_013 / HIGH_CONNECTION_MUSIC_LOOKUP

### 목적
연결 수가 많은 음악 조회

### Tool

```python
lookup_high_connection_music(limit: int = 20)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[r]-()
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  count(r) AS relation_count,
  m.track_popularity AS popularity
ORDER BY relation_count DESC, popularity DESC
LIMIT coalesce($limit, 20)
```

### 예상 질문
- 가장 많이 연결된 음악 보여줘
- 그래프에서 중심에 가까운 노래가 뭐야?
- 연결 정보가 많은 곡 알려줘
- 추천 근거가 많은 음악 찾아줘
- 노드 연결이 많은 음악 순위 보여줘

---

## Q_SEARCH_014 / RELATION_TYPE_LOOKUP

### 목적
특정 음악의 관계 타입 목록 조회

### Tool

```python
lookup_music_relation_types(keyword: str, limit: int = 20)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[r]-()
WHERE toLower(m.track_name) CONTAINS toLower($keyword)
RETURN DISTINCT
  type(r) AS relation_type
LIMIT coalesce($limit, 20)
```

### 예상 질문
- Ditto는 어떤 관계들이 있어?
- 이 노래랑 연결된 엣지 타입 보여줘
- Hype Boy의 관계 종류 알려줘
- 이 곡은 어떤 정보랑 연결될 수 있어?
- Attention의 연결 타입 목록 보여줘

---

# 5. RECOMMENDATION Query Types

---

## Q_REC_001 / GENRE_BASED_RECOMMENDATION

### 목적
장르 기반 추천

### Tool

```python
recommend_by_genre(genre: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE toLower(m.playlist_genre) = toLower($genre)
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.playlist_genre AS genre,
  coalesce(m.track_popularity, 0) AS popularity,
  coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- pop 노래 추천해줘
- rock 음악 추천해줘
- 힙합 추천해줘
- dance 장르로 들을 만한 곡 있어?
- edm 노래 추천해줘

---

## Q_REC_002 / MOOD_BASED_RECOMMENDATION

### 목적
감정/분위기 기반 추천

### Tool

```python
recommend_by_mood(mood: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[:HAS_LABEL_EMOTION]-(emo:LabelEmotion)
WHERE toLower(emo.name) CONTAINS toLower($mood)
RETURN DISTINCT
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  emo.name AS matched_mood,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 우울할 때 들을 노래 추천해줘
- 기분 좋아지는 음악 추천해줘
- 잔잔한 분위기 음악 추천해줘
- 신나는 노래 추천해줘
- 차분한 곡 추천해줘

---

## Q_REC_003 / SITUATION_BASED_RECOMMENDATION

### 목적
상황 기반 추천

### Tool

```python
recommend_by_situation(situation: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[]-(s:Situation)
WHERE toLower(s.name) CONTAINS toLower($situation)
RETURN DISTINCT
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  s.name AS matched_situation,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 운동할 때 들을 노래 추천해줘
- 공부할 때 듣기 좋은 음악 추천해줘
- 출근길에 들을 음악 추천해줘
- 밤 산책할 때 들을 노래 추천해줘
- 드라이브할 때 들을 곡 추천해줘

---

## Q_REC_004 / WEATHER_BASED_RECOMMENDATION

### 목적
날씨 기반 추천

### Tool

```python
recommend_by_weather(weather: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)-[]-(w:Weather)
WHERE toLower(w.name) CONTAINS toLower($weather)
RETURN DISTINCT
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  w.name AS matched_weather,
  coalesce(m.track_popularity, 0) AS popularity,
  10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 비 오는 날 들을 노래 추천해줘
- 맑은 날 어울리는 음악 추천해줘
- 눈 오는 날 듣기 좋은 곡 있어?
- 흐린 날 들을 만한 음악 추천해줘
- 더운 날 듣기 좋은 노래 추천해줘

---

## Q_REC_005 / SIMILAR_SONG_RECOMMENDATION

### 목적
특정 곡 기반 유사 추천

### Tool

```python
recommend_similar_song(keyword: str, limit: int = 10)
```

### Cypher

```cypher
MATCH (base:MusicCatalog)-[]-(feature)<-[]-(rec:MusicCatalog)
WHERE toLower(base.track_name) CONTAINS toLower($keyword)
  AND base.content_id <> rec.content_id
WITH rec, count(DISTINCT feature) AS matched_feature_count
RETURN
  rec.content_id AS content_id,
  rec.track_name AS track_name,
  rec.track_artist AS track_artist,
  matched_feature_count,
  coalesce(rec.track_popularity, 0) AS popularity,
  matched_feature_count * 10 + coalesce(rec.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- Ditto 같은 노래 추천해줘
- Hype Boy랑 비슷한 노래 추천해줘
- 이 곡이 마음에 드는데 비슷한 곡 있어?
- Shape of You 느낌으로 추천해줘
- Attention 비슷한 음악 들려줘

---

## Q_REC_006 / POPULARITY_BASED_RECOMMENDATION

### 목적
인기 기반 추천

### Tool

```python
recommend_by_popularity(
    genre=None,
    subgenre=None,
    artist=None,
    limit=10,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE
  ($genre IS NULL OR toLower(m.playlist_genre) = toLower($genre))
  AND ($subgenre IS NULL OR toLower(m.playlist_subgenre) = toLower($subgenre))
  AND ($artist IS NULL OR toLower(m.track_artist) CONTAINS toLower($artist))
RETURN
  m.content_id AS content_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  m.playlist_genre AS genre,
  coalesce(m.track_popularity, 0) AS popularity,
  coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 인기 많은 노래 추천해줘
- 요즘 들을 만한 유명한 곡 추천해줘
- pop 인기곡 추천해줘
- 가장 인기 있는 음악 보여줘
- 대중적인 노래 추천해줘

---

## Q_REC_007 / DIVERSITY_RECOMMENDATION

### 목적
다양성 기반 추천

### Tool

```python
recommend_diverse_music(
    genre=None,
    mood=None,
    situation=None,
    weather=None,
    limit=10,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
WHERE ($genre IS NULL OR toLower(m.playlist_genre) = toLower($genre))
WITH m
ORDER BY coalesce(m.track_popularity, 0) DESC
WITH m.track_artist AS artist, collect(m)[0] AS top_music
RETURN
  top_music.content_id AS content_id,
  top_music.track_name AS track_name,
  top_music.track_artist AS track_artist,
  top_music.playlist_genre AS genre,
  coalesce(top_music.track_popularity, 0) AS popularity,
  coalesce(top_music.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 다양하게 노래 추천해줘
- 아티스트 안 겹치게 추천해줘
- pop 노래 여러 가수로 추천해줘
- 비슷한 노래 말고 다양하게 보여줘
- 장르 안에서 다양하게 골라줘

---

## Q_REC_008 / HYBRID_CONTEXT_RECOMMENDATION

### 목적
복합 맥락 기반 추천

### Tool

```python
recommend_by_hybrid_context(
    genre=None,
    mood=None,
    situation=None,
    weather=None,
    limit=10,
)
```

### Cypher

```cypher
MATCH (m:MusicCatalog)
OPTIONAL MATCH (m)-[:HAS_GENRE]-(g:Genre)
OPTIONAL MATCH (m)-[:HAS_LABEL_EMOTION]-(emo:LabelEmotion)
OPTIONAL MATCH (m)-[:HAS_LABEL_EXERCISE|HAS_LABEL_COMMUTE|HAS_LABEL_HOME|HAS_LABEL_FOCUS|HAS_LABEL_SPECIAL|HAS_LABEL_TIME|HAS_LABEL_SEASON|HAS_LABEL_EMOTION_SIT]-(s)
OPTIONAL MATCH (m)-[:HAS_LABEL_WEATHER]-(w:LabelWeather)
WITH m,
  max(CASE WHEN $genre IS NOT NULL AND toLower(g.genre) = toLower($genre) THEN 1 ELSE 0 END) AS genre_match,
  max(CASE WHEN $mood IS NOT NULL AND toLower(emo.name) CONTAINS toLower($mood) THEN 1 ELSE 0 END) AS mood_match,
  max(CASE WHEN $situation IS NOT NULL AND toLower(s.name) CONTAINS toLower($situation) THEN 1 ELSE 0 END) AS situation_match,
  max(CASE WHEN $weather IS NOT NULL AND toLower(w.name) CONTAINS toLower($weather) THEN 1 ELSE 0 END) AS weather_match
WITH m,
  genre_match + mood_match + situation_match + weather_match AS matched_count
WHERE matched_count > 0
RETURN
  m.track_id AS track_id,
  m.track_name AS track_name,
  m.track_artist AS track_artist,
  matched_count,
  coalesce(m.track_popularity, 0) AS popularity,
  matched_count * 10 + coalesce(m.track_popularity, 0) AS recommendation_score
ORDER BY recommendation_score DESC
LIMIT coalesce($limit, 10)
```

### 예상 질문
- 비 오는 날 들을 잔잔한 노래 추천해줘
- 운동할 때 신나는 pop 추천해줘
- 밤에 듣기 좋은 감성 음악 추천해줘
- 기분 전환할 때 들을 밝은 노래 추천해줘
- 출근길에 듣기 좋은 에너지 있는 곡 추천해줘

---

# 6. Router 분류 규칙

## 1차 분류

```text
- SEARCH
- RECOMMENDATION
```

---

## 2차 분류

```text
- MUSIC_BASIC_INFO_LOOKUP
- MUSIC_RELATION_INFO_LOOKUP
- MUSIC_CONDITION_SEARCH
- SIMILAR_MUSIC_LOOKUP
- ...
- HYBRID_CONTEXT_RECOMMENDATION
```

---

## 추천형 키워드 예시

추천형으로 분류:
- 추천해줘
- 골라줘
- 들을 만한
- 어울리는 곡
- 비슷한 곡 추천

검색형으로 분류:
- 찾아줘
- 보여줘
- 정보 알려줘
- 뭐야
- 목록 보여줘

---

# 7. MVP 구현 규칙

## 금지

- Agent가 Cypher 직접 생성
- LLM이 DB 구조 수정
- 존재하지 않는 추천 생성
- 하드코딩된 쿼리 생성

---

## 필수

- 모든 Query는 Tool 함수로 호출
- Query는 상수화
- Query Type 고정
- 반환 JSON 구조 통일
- recommendation_score 반환
- status 반환

---

# 8. 향후 확장 방향

향후 추가 가능:
- Full-text index
- Embedding similarity
- Vector Search
- Graph Data Science
- Personalized reranking
- User history 기반 추천
- Session memory 기반 추천
- RAG 기반 추천 이유 생성

