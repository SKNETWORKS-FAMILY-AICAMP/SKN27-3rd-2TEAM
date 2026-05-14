def merge_unique(new_items: list, existing: list, limit: int) -> list:
    """new_items를 앞에 두고 existing에서 중복 제거 후 limit 개수를 유지한다."""
    merged = list(new_items) + [x for x in existing if x not in new_items]
    return merged[:limit]
