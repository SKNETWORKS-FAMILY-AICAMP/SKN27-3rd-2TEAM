# Common Constants / State 기준

공통 계약 상수와 기본 state는 `app/common`을 source of truth로 사용한다.

## 관리 대상

- `app/common/constants.py`: `DEFAULT_USER_ID`, 공통 `status` 허용값
- `app/common/default_state.py`: `SESSION_DEFAULTS`, `DEFAULT_ML_OUTPUT`, `FALLBACK_RESPONSE_STATE`
- `app/common/labels.py`: 추천 category 표시 label

## 유지 대상

레이어 책임이 명확한 상수는 기존 위치를 유지한다.

- SQL 쿼리 상수는 Repository Layer 책임이므로 `app/repositories/query_constants.py`에 둔다.
- UI 색상, spacing, radius 같은 theme 상수는 UI Layer 책임이므로 `app/ui/styles/theme.py`에 둔다.

## 사용 규칙

- Service, Validator, Agent가 공유하는 계약 상수와 기본 state는 `app.common`에서 import한다.
- `app/services/default_state.py`는 기존 import 호환을 위한 얇은 재노출 파일이며, 새 코드는 `app.common.default_state`를 직접 사용한다.
- 새로운 공통 상수를 추가할 때는 먼저 문서 계약에 있는 값인지 확인한다.
