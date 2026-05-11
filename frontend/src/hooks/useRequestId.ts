import { useRef } from "react";
import { generateRequestId } from "../utils/requestId";

/**
 * 컴포넌트 마운트 수명 동안 동일한 requestId를 반환한다.
 * React Query retry 시 같은 ID를 재사용 → 백엔드 lifecycle cache 중복 차단과 연동된다.
 * 컴포넌트가 unmount/remount 되면 새 ID가 생성된다.
 */
export function useRequestId(): string {
  const ref = useRef(generateRequestId());
  return ref.current;
}

/**
 * key가 바뀔 때마다 새 requestId를 생성하고, 같은 key에서는 동일 ID를 반환한다.
 * 예: Music Detail 모달에서 content_id가 바뀔 때마다 새 ID가 필요한 경우에 사용한다.
 */
export function useRequestIdPerKey(key: string | null | undefined): string {
  const map = useRef<Record<string, string>>({});
  if (key != null && !map.current[key]) {
    map.current[key] = generateRequestId();
  }
  return key != null ? map.current[key] : generateRequestId();
}
