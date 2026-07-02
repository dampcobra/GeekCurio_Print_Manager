def format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_weight(grams: float) -> str:
    if grams >= 1000:
        return f"{grams / 1000:.2f} kg"
    return f"{grams:.1f} g"
