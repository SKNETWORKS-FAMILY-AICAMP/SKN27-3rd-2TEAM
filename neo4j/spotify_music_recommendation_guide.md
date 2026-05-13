# 🎵 Spotify 데이터 기반 음악 추천 시스템 — 상황별 컬럼 활용 가이드

---

## 📌 핵심 컬럼 요약

| 컬럼 | 역할 | 범위 |
|------|------|------|
| `energy` | 활기·강도 | 0.0 ~ 1.0 |
| `valence` | 감정 긍정성 | 0.0 ~ 1.0 |
| `danceability` | 리듬감·댄스 적합도 | 0.0 ~ 1.0 |
| `tempo` | 빠르기 (BPM) | 수치 |
| `acousticness` | 어쿠스틱 비율 | 0.0 ~ 1.0 |
| `instrumentalness` | 연주곡 여부 (보컬 없음) | 0.0 ~ 1.0 |
| `speechiness` | 말소리 비율 | 0.0 ~ 1.0 |
| `loudness` | 음량 (dB) | -60 ~ 0 |
| `liveness` | 라이브 느낌 | 0.0 ~ 1.0 |
| `mode` | 장조(1) / 단조(0) | 0 또는 1 |

---

## 🌤️ 날씨별

| 날씨 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **맑음** | `valence`, `energy`, `mode` | valence ≥ 0.6, energy ≥ 0.5, mode = 1 | 밝고 경쾌한 장조 곡 |
| **비** | `valence`, `acousticness`, `mode`, `tempo` | valence ≤ 0.4, acousticness ≥ 0.5, mode = 0, tempo 60~90 | 차분하고 감성적인 단조 |
| **눈** | `acousticness`, `instrumentalness`, `valence` | acousticness ≥ 0.6, valence 0.3~0.6, tempo ≤ 80 | 고요하고 포근한 느낌 |
| **흐림** | `valence`, `energy`, `mode` | valence 0.3~0.5, energy 0.3~0.5, mode = 0 | 무겁지 않지만 차분함 |

---

## 🌸 계절별

| 계절 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **봄** | `valence`, `energy`, `acousticness`, `tempo` | valence ≥ 0.6, energy 0.4~0.7, acousticness ≥ 0.4, tempo 90~120 | 설레고 가볍고 따뜻한 느낌 |
| **여름** | `energy`, `danceability`, `valence`, `tempo` | energy ≥ 0.7, danceability ≥ 0.6, valence ≥ 0.6, tempo ≥ 120 | 강렬하고 신나는 비트 |
| **가을** | `valence`, `acousticness`, `mode`, `instrumentalness` | valence 0.3~0.5, acousticness ≥ 0.5, mode = 0 | 감성적이고 쓸쓸한 무드 |
| **겨울** | `acousticness`, `valence`, `energy`, `instrumentalness` | acousticness ≥ 0.5, valence ≤ 0.4, energy ≤ 0.4 | 고요하고 내면적인 분위기 |

---

## 💭 감정별

| 감정 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **외로움** | `valence`, `acousticness`, `mode`, `instrumentalness` | valence ≤ 0.3, acousticness ≥ 0.6, mode = 0 | 감성 어쿠스틱, 조용한 단조 |
| **우울함** | `valence`, `mode`, `energy`, `tempo` | valence ≤ 0.3, mode = 0, energy ≤ 0.4, tempo ≤ 80 | 느리고 어두운 단조 곡 |
| **신남** | `energy`, `danceability`, `valence`, `tempo` | energy ≥ 0.8, danceability ≥ 0.7, valence ≥ 0.7, tempo ≥ 120 | 고에너지, 빠른 리듬 |
| **설렘** | `valence`, `energy`, `mode`, `tempo` | valence ≥ 0.6, energy 0.5~0.7, mode = 1, tempo 100~130 | 두근거리고 밝은 장조 |

---

## 🕐 시간대별

| 시간대 | 주요 컬럼 | 권장 값 | 이유 |
|--------|-----------|---------|------|
| **아침** | `energy`, `valence`, `tempo`, `mode` | energy 0.5~0.7, valence ≥ 0.6, tempo 100~120, mode = 1 | 기분 좋게 하루 시작 |
| **오후** | `energy`, `danceability`, `valence` | energy 0.5~0.8, valence 0.5~0.8 | 활동적이고 중립적 |
| **저녁** | `valence`, `acousticness`, `energy`, `tempo` | valence 0.3~0.6, acousticness ≥ 0.4, energy ≤ 0.5 | 하루를 정리하는 차분함 |
| **밤** | `acousticness`, `instrumentalness`, `energy`, `tempo` | acousticness ≥ 0.5, energy ≤ 0.4, tempo ≤ 90 | 조용하고 감성적 |
| **새벽** | `instrumentalness`, `acousticness`, `energy`, `loudness` | instrumentalness ≥ 0.5, energy ≤ 0.3, loudness ≤ -10 | 극도로 조용하고 몽환적 |

---

## ⚡ 에너지 레벨별

| 레벨 | 주요 컬럼 | 권장 값 |
|------|-----------|---------|
| **잔잔함** | `energy`, `tempo`, `acousticness`, `loudness` | energy ≤ 0.4, tempo ≤ 90, acousticness ≥ 0.5, loudness ≤ -8 |
| **보통** | `energy`, `tempo`, `valence` | energy 0.4~0.7, tempo 90~120 |
| **신남** | `energy`, `danceability`, `tempo`, `loudness` | energy ≥ 0.7, danceability ≥ 0.7, tempo ≥ 120 |

---

## 🎯 상황별 상세

### 🚶 이동

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **출근길** | `energy`, `valence`, `tempo`, `mode` | energy 0.5~0.7, valence ≥ 0.5, tempo 100~120, mode = 1 | 활기차게 하루 시작, 너무 강하지 않게 |
| **퇴근길** | `valence`, `energy`, `acousticness`, `mode` | valence 0.3~0.6, energy ≤ 0.5, acousticness ≥ 0.3 | 하루 피로 해소, 감성적 전환 |
| **대중교통** | `instrumentalness`, `energy`, `speechiness` | instrumentalness ≥ 0.4, energy 0.3~0.6, speechiness ≤ 0.1 | 집중 방해 없이 편안하게 |
| **드라이브** | `energy`, `tempo`, `danceability`, `valence` | energy 0.6~0.8, tempo 110~140, danceability ≥ 0.6, valence ≥ 0.5 | 신나고 리듬감 있는 드라이빙 |

---

### 🏠 집

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **집안일** | `energy`, `danceability`, `tempo`, `valence` | energy 0.5~0.7, danceability ≥ 0.6, valence ≥ 0.5 | 활기차고 리듬감 있어 일이 신남 |
| **요리** | `valence`, `tempo`, `danceability` | valence ≥ 0.5, tempo 100~130, danceability 0.5~0.7 | 흥겹지만 과하지 않은 리듬 |
| **샤워** | `energy`, `valence`, `danceability` | energy ≥ 0.6, valence ≥ 0.6 | 신나고 따라 부르기 좋은 곡 |
| **쉬는 중** | `acousticness`, `energy`, `instrumentalness`, `valence` | acousticness ≥ 0.5, energy ≤ 0.4, instrumentalness ≥ 0.3 | 몸과 마음을 편안하게 |
| **잠들기 전** | `energy`, `tempo`, `acousticness`, `instrumentalness`, `loudness` | energy ≤ 0.3, tempo ≤ 70, acousticness ≥ 0.6, loudness ≤ -10 | 수면 유도, 극도로 잔잔하게 |

---

### 📚 집중

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **공부 / 독서** | `instrumentalness`, `speechiness`, `energy`, `tempo` | instrumentalness ≥ 0.7, speechiness ≤ 0.05, energy 0.3~0.5 | 가사 없이 집중력 유지 |
| **코딩 / 업무** | `instrumentalness`, `energy`, `tempo` | instrumentalness ≥ 0.6, energy 0.4~0.6, tempo 90~120 | 적당한 리듬으로 흐름 유지 |
| **과제 마감** | `energy`, `tempo`, `instrumentalness` | energy 0.6~0.8, tempo ≥ 120, instrumentalness ≥ 0.5 | 긴박감 있는 고에너지 연주곡 |

---

### 🏃 운동 / 활동

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **운동 (헬스 / 러닝)** | `energy`, `tempo`, `danceability`, `loudness` | energy ≥ 0.8, tempo ≥ 130, danceability ≥ 0.7, loudness ≥ -6 | 최고 강도, 강렬한 비트 |
| **산책** | `valence`, `energy`, `tempo`, `acousticness` | valence ≥ 0.5, energy 0.4~0.6, tempo 90~110 | 가볍고 산뜻한 느낌 |
| **스트레칭 / 요가** | `energy`, `acousticness`, `tempo`, `instrumentalness` | energy ≤ 0.4, acousticness ≥ 0.5, tempo ≤ 80 | 부드럽고 유연한 흐름 |

---

### 👫 관계 / 이벤트

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **데이트** | `valence`, `acousticness`, `mode`, `energy`, `tempo` | valence ≥ 0.5, acousticness ≥ 0.3, mode = 1, energy 0.4~0.6 | 낭만적이고 설레는 분위기 |
| **친구 모임** | `danceability`, `energy`, `valence`, `tempo` | danceability ≥ 0.6, energy ≥ 0.6, valence ≥ 0.6 | 흥겹고 에너지 넘치는 분위기 |
| **생일 / 기념일** | `valence`, `energy`, `danceability`, `mode` | valence ≥ 0.7, energy ≥ 0.6, mode = 1 | 축제적이고 화사한 느낌 |
| **홈파티** | `danceability`, `energy`, `valence`, `tempo`, `loudness` | danceability ≥ 0.7, energy ≥ 0.7, valence ≥ 0.6, tempo ≥ 110 | 파티 분위기, 춤추기 좋은 |

---

### 💔 감정 상황

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **이별 후** | `valence`, `mode`, `acousticness`, `energy` | valence ≤ 0.3, mode = 0, acousticness ≥ 0.4, energy ≤ 0.4 | 감성적이고 슬픈 단조 |
| **위로 필요** | `valence`, `acousticness`, `mode`, `tempo` | valence 0.3~0.5, acousticness ≥ 0.5, tempo ≤ 90 | 공감해주는 느낌, 너무 슬프지 않게 |
| **기분 전환** | `valence`, `energy`, `danceability`, `mode` | valence ≥ 0.6, energy ≥ 0.6, mode = 1 | 긍정 에너지 주입 |
| **추억 회상** | `valence`, `acousticness`, `mode`, `liveness` | valence 0.4~0.7, acousticness ≥ 0.4 | 따뜻하고 nostalgic한 느낌 |

---

### ✈️ 여행

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **여행 준비** | `valence`, `energy`, `danceability` | valence ≥ 0.6, energy ≥ 0.6, danceability ≥ 0.5 | 설레고 기대감 넘치는 |
| **공항 / 기차** | `instrumentalness`, `acousticness`, `energy` | instrumentalness ≥ 0.4, energy 0.3~0.5 | 창밖 보며 감상하기 좋은 |
| **여행 중 (드라이브 / 버스)** | `energy`, `valence`, `tempo`, `danceability` | energy 0.6~0.8, valence ≥ 0.6, tempo 110~130 | 여행 감성 극대화 |

---

### 🎪 특수 상황

| 상황 | 주요 컬럼 | 권장 값 | 이유 |
|------|-----------|---------|------|
| **카페** | `acousticness`, `instrumentalness`, `energy`, `tempo` | acousticness ≥ 0.5, energy 0.2~0.5, instrumentalness ≥ 0.4, tempo 70~100 | 배경음악으로 방해 없는 |
| **클럽** | `danceability`, `energy`, `tempo`, `loudness` | danceability ≥ 0.8, energy ≥ 0.8, tempo ≥ 125, loudness ≥ -5 | 최대 댄스 에너지 |
| **페스티벌 / 콘서트** | `energy`, `liveness`, `danceability`, `valence` | energy ≥ 0.8, liveness ≥ 0.5, danceability ≥ 0.7 | 라이브 현장감, 고에너지 |
| **게임** | `energy`, `tempo`, `instrumentalness` | energy 0.6~0.9, tempo ≥ 120, instrumentalness ≥ 0.5 | 몰입감 있는 BGM |
| **감성 / 새벽 감성** | `valence`, `acousticness`, `mode`, `instrumentalness`, `energy` | valence ≤ 0.4, acousticness ≥ 0.6, mode = 0, energy ≤ 0.3 | 몽환적이고 내면적 |

---

## 🛠️ 추천 시스템 구현 팁

상황 키워드를 입력받으면 아래 우선순위로 컬럼을 필터링하는 방식을 권장합니다.

```
1순위: energy + valence        → 전체 무드 결정
2순위: tempo                   → 빠르기 조절
3순위: acousticness + instrumentalness → 음색 / 가사 여부
4순위: mode + danceability     → 세부 감성 튜닝
```

> - `speechiness`는 **랩·보컬 트랙 제외** 목적으로 보조 필터로 활용
> - `liveness`는 **라이브 감성** 강조 시 보조 필터로 활용
> - `loudness`는 에너지 레벨 미세 조정 시 활용 (운동/클럽 등 고강도 상황)
