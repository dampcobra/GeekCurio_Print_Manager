from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FilamentUsage:
    filament_id: int
    type: str
    used_g: float
    color: str | None = None
    used_m: float | None = None


@dataclass(frozen=True, slots=True)
class PlateSummary:
    index: int
    print_time_s: int
    weight_g: float
    filaments: tuple[FilamentUsage, ...] = field(default_factory=tuple)
    support_used: bool | None = None
    printer_model_id: str | None = None


@dataclass(frozen=True, slots=True)
class PrintJob:
    source_path: Path
    slicer: str
    plates: tuple[PlateSummary, ...] = field(default_factory=tuple)

    @property
    def total_print_time_s(self) -> int:
        return sum(plate.print_time_s for plate in self.plates)

    @property
    def total_weight_g(self) -> float:
        return sum(plate.weight_g for plate in self.plates)

    def filament_totals_by_material(self) -> dict[tuple[str, str | None], float]:
        totals: dict[tuple[str, str | None], float] = {}
        for plate in self.plates:
            for filament in plate.filaments:
                key = (filament.type, filament.color)
                totals[key] = totals.get(key, 0.0) + filament.used_g
        return totals
