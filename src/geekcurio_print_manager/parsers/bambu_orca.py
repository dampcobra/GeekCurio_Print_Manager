import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from geekcurio_print_manager.exceptions import SliceMetadataParseError
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.parsers.base import SlicerProjectParser

SLICE_INFO_PATH = "Metadata/slice_info.config"
SLICER_NAME = "bambu_studio_orcaslicer"


class BambuOrcaParser(SlicerProjectParser):
    """Reads Metadata/slice_info.config as written by Bambu Studio and OrcaSlicer."""

    def can_parse(self, archive: zipfile.ZipFile) -> bool:
        return SLICE_INFO_PATH in archive.namelist()

    def parse(self, archive: zipfile.ZipFile, source_path: Path) -> PrintJob:
        raw = archive.read(SLICE_INFO_PATH)
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise SliceMetadataParseError(source_path, "slice_info.config isn't valid XML") from exc

        plate_elements = root.findall("plate")
        if not plate_elements:
            raise SliceMetadataParseError(source_path, "no plate data found in slice_info.config")

        plates = tuple(
            self._parse_plate(plate_element, source_path)
            for plate_element in plate_elements
        )
        return PrintJob(source_path=source_path, slicer=SLICER_NAME, plates=plates)

    def _parse_plate(self, plate_element: ET.Element, source_path: Path) -> PlateSummary:
        metadata = {
            entry.get("key"): entry.get("value")
            for entry in plate_element.findall("metadata")
        }

        index = self._parse_int(metadata.get("index"), source_path, "plate 'index'")
        print_time_s = self._parse_int(
            metadata.get("prediction"), source_path, f"plate {index} 'prediction'"
        )
        weight_g = self._parse_float(
            metadata.get("weight"), source_path, f"plate {index} 'weight'"
        )

        filaments = tuple(
            self._parse_filament(filament_element, source_path, index)
            for filament_element in plate_element.findall("filament")
        )

        return PlateSummary(
            index=index,
            print_time_s=print_time_s,
            weight_g=weight_g,
            filaments=filaments,
            support_used=self._parse_optional_bool(metadata.get("support_used")),
            printer_model_id=metadata.get("printer_model_id"),
        )

    def _parse_filament(
        self, filament_element: ET.Element, source_path: Path, plate_index: int
    ) -> FilamentUsage:
        filament_id = self._parse_int(
            filament_element.get("id"), source_path, f"plate {plate_index} filament 'id'"
        )
        filament_type = filament_element.get("type")
        if not filament_type:
            raise SliceMetadataParseError(
                source_path, f"plate {plate_index} filament {filament_id} is missing a 'type'"
            )
        used_g = self._parse_float(
            filament_element.get("used_g"),
            source_path,
            f"plate {plate_index} filament {filament_id} 'used_g'",
        )
        used_m_raw = filament_element.get("used_m")
        used_m = (
            self._parse_float(used_m_raw, source_path, f"plate {plate_index} filament {filament_id} 'used_m'")
            if used_m_raw is not None
            else None
        )

        return FilamentUsage(
            filament_id=filament_id,
            type=filament_type,
            used_g=used_g,
            color=filament_element.get("color"),
            used_m=used_m,
        )

    @staticmethod
    def _parse_int(value: str | None, source_path: Path, field_name: str) -> int:
        if value is None:
            raise SliceMetadataParseError(source_path, f"missing {field_name}")
        try:
            return int(float(value))
        except ValueError as exc:
            raise SliceMetadataParseError(source_path, f"invalid {field_name}: '{value}'") from exc

    @staticmethod
    def _parse_float(value: str | None, source_path: Path, field_name: str) -> float:
        if value is None:
            raise SliceMetadataParseError(source_path, f"missing {field_name}")
        try:
            return float(value)
        except ValueError as exc:
            raise SliceMetadataParseError(source_path, f"invalid {field_name}: '{value}'") from exc

    @staticmethod
    def _parse_optional_bool(value: str | None) -> bool | None:
        if value is None:
            return None
        return value.strip().lower() == "true"
