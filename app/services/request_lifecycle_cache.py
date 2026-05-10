class DuplicateRequestError(RuntimeError):
    """동일 request_id가 처리 중일 때 발생한다."""


class RequestLifecycleCache:
    """단일 프로세스 내 request_id 중복 실행을 차단한다."""

    def __init__(self):
        self._inflight: set[str] = set()

    def start(self, request_id: str) -> None:
        if request_id in self._inflight:
            raise DuplicateRequestError(f"duplicate inflight request: {request_id}")
        self._inflight.add(request_id)

    def finish(self, request_id: str) -> None:
        self._inflight.discard(request_id)


request_lifecycle_cache = RequestLifecycleCache()
