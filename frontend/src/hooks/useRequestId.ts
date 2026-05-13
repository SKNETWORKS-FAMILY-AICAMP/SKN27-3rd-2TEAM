import { useRef } from "react";
import { generateRequestId } from "../utils/requestId";

/**
 * 컴포넌트 생명주기 동안 같은 requestId를 반환한다.
 * React Query retry 시 같은 ID를 재사용해 백엔드 lifecycle cache 중복 차단과 연동한다.
 */
export function useRequestId(): string {
  const ref = useRef(generateRequestId());
  // requestId는 렌더링 결과가 아니라 API 중복 방지 계약을 위한 안정 값이다.
  // eslint-disable-next-line react-hooks/refs
  return ref.current;
}

/**
 * key가 바뀔 때마다 requestId를 생성하고, 같은 key에서는 같은 ID를 반환한다.
 * Music Detail 모달에서 content_id별 요청 ID를 유지하기 위해 기존 동작을 보존한다.
 */
export function useRequestIdPerKey(key: string | null | undefined): string {
  const map = useRef<Record<string, string>>({});
  // eslint-disable-next-line react-hooks/refs
  if (key != null && !map.current[key]) {
    // eslint-disable-next-line react-hooks/refs
    map.current[key] = generateRequestId();
  }
  // eslint-disable-next-line react-hooks/refs
  return key != null ? map.current[key] : generateRequestId();
}
