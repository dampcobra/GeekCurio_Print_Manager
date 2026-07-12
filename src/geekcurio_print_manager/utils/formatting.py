import math
from pathlib import Path

_DISPLAY_STRIP_EXTS = frozenset({".3mf", ".gcode"})


def display_project_name(source_file: str) -> str:
    """Return a customer-facing project name from a source filename.

    Strips known slicer extensions iteratively:
      DriftPostBase.gcode.3mf -> DriftPostBase
      DriftPostBase.3mf       -> DriftPostBase
      normal-project-name     -> normal-project-name
    """
    name = Path(source_file).name
    while True:
        p = Path(name)
        if p.suffix.lower() in _DISPLAY_STRIP_EXTS:
            name = p.stem
        else:
            break
    return name


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_duration_hm(seconds: int) -> str:
    """Format seconds as hours and minutes, rounding up to the nearest minute.

    Used for customer/operator-facing display where estimates should never
    appear shorter than the actual slicer value.

      6057s (1h 40m 57s) -> "1h 41m"
      6001s (1h 40m 01s) -> "1h 41m"
      5400s (1h 30m 00s) -> "1h 30m"
      2364s (39m 24s)    -> "40m"
    """
    total_minutes = math.ceil(int(seconds) / 60)
    h, m = divmod(total_minutes, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def format_weight(grams: float) -> str:
    if grams >= 1000:
        return f"{grams / 1000:.2f} kg"
    return f"{grams:.1f} g"
