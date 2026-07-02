from pathlib import Path

from geekcurio_print_manager.exceptions import ProjectFileNotFoundError, SliceMetadataNotFoundError
from geekcurio_print_manager.models.print_job import PrintJob
from geekcurio_print_manager.parsers.bambu_orca import BambuOrcaParser
from geekcurio_print_manager.parsers.base import SlicerProjectParser
from geekcurio_print_manager.utils.archive import ensure_3mf_skeleton, open_archive


class InspectionService:
    """Single entry point for turning a 3MF file path into a validated PrintJob."""

    def __init__(self, parsers: tuple[SlicerProjectParser, ...] | None = None) -> None:
        self._parsers = parsers if parsers is not None else (BambuOrcaParser(),)

    def inspect(self, path: str | Path) -> PrintJob:
        path = Path(path)
        if not path.is_file():
            raise ProjectFileNotFoundError(path)

        with open_archive(path, display_path=path) as archive:
            ensure_3mf_skeleton(archive, display_path=path)

            for parser in self._parsers:
                if parser.can_parse(archive):
                    return parser.parse(archive, path)

            raise SliceMetadataNotFoundError(path)
