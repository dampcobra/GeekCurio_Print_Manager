import zipfile
from abc import ABC, abstractmethod
from pathlib import Path

from geekcurio_print_manager.models.print_job import PrintJob


class SlicerProjectParser(ABC):
    """Interface for extracting a PrintJob from an already-opened 3MF archive."""

    @abstractmethod
    def can_parse(self, archive: zipfile.ZipFile) -> bool:
        """Return True if this parser recognises the archive's slicer-specific metadata."""

    @abstractmethod
    def parse(self, archive: zipfile.ZipFile, source_path: Path) -> PrintJob:
        """Extract a PrintJob from the archive. Raises SliceMetadataError on failure."""
