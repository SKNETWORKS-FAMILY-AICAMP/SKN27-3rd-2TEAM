from enum import StrEnum


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_MATCH = "partial_match"
    EMPTY_RESULT = "empty_result"
    TIMEOUT = "timeout"
    ERROR = "error"
