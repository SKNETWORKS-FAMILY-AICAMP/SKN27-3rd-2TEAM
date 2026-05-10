import json
import logging
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


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    # suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
