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


def format_weight(grams: float) -> str:
    if grams >= 1000:
        return f"{grams / 1000:.2f} kg"
    return f"{grams:.1f} g"
