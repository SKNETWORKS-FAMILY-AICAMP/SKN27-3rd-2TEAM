# Ranking Policy

구현 기준: `app/policies/ranking_policy.py`

---

## 목적

RAG evidence 내에서 개별 트랙의 랭킹 점수를 계산하는 정책을 정의한다.  
점수는 RecommendationAgent가 카테고리 내 우선순위를 결정할 때 보조적으로 사용한다.

---

## 점수 계산 공식

```
score = max(MIN_SCORE, BASE_SCORE - ((rank - 1) * RANK_DECAY))
```

| 상수        | 값    | 의미 |
|------------|-------|------|
| MIN_SCORE  | 0.10  | 점수 하한선 |
| BASE_SCORE | 1.00  | 1위 점수 |
| RANK_DECAY | 0.05  | 순위당 감소량 |

### 예시

| rank | score |
|------|-------|
| 1    | 1.00  |
| 2    | 0.95  |
| 3    | 0.90  |
| 19   | 0.10  |
| 20+  | 0.10  |

---

## 판단 기준

- rank는 1 이상의 정수여야 한다. 0 이하이면 ValueError를 발생시킨다.
- 점수는 MIN_SCORE 아래로 내려가지 않는다.

---

## 금지 사항

- LLM이 점수를 계산하거나 순위를 조정하지 않는다.
- 점수 기반으로 카테고리 섹션을 변경하지 않는다.
- 점수만으로 추천 여부를 결정하지 않는다 (카테고리 우선순위가 우선).

---

## 운영 관점

- 점수 상수 변경 시 이 문서와 `ranking_policy.py`를 동시에 수정한다.
- 점수 계산은 deterministic하며 외부 의존성이 없다.
