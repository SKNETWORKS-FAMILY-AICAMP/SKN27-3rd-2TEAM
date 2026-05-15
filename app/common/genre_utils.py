def normalize_genre_tokens(value) -> set[str]:
    if value is None:
        return set()

    if isinstance(value, str):
        raw_values = [value]
    else:
        try:
            raw_values = list(value)
        except TypeError:
            raw_values = [value]

    tokens = set()
    for raw_value in raw_values:
        for token in str(raw_value).split(","):
            text = token.strip().casefold()
            if text:
                tokens.add(text)
    return tokens
