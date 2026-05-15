import json
import logging
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    _SKIP = frozenset({
        "msg", "args", "levelname", "levelno", "name", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        log: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log["exc"] = self.formatException(record.exc_info)
        for key, val in record.__dict__.items():
            if key in self._SKIP:
                continue
            try:
                json.dumps(val)
                log[key] = val
            except (TypeError, ValueError):
                log[key] = str(val)
        return json.dumps(log, ensure_ascii=False)


def setup_logging(level: str | None = None) -> None:
    effective_level = (level or os.getenv("LOG_LEVEL", "ERROR")).upper()
    root = logging.getLogger()
    root.setLevel(effective_level)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    # 운영 기본값은 오류 로그만 출력한다. 필요 시 LOG_LEVEL로 낮출 수 있다.
    for noisy in ("uvicorn.access", "uvicorn.error", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(effective_level)
