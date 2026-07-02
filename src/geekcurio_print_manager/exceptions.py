from pathlib import Path


class PrintManagerError(Exception):
    """Base class for all application-raised errors. Never raised directly."""


class ProjectFileError(PrintManagerError):
    """Base class for problems with the file itself, before any 3MF parsing begins."""


class ProjectFileNotFoundError(ProjectFileError):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f"Could not find a file at '{path}'. Check the path and try again."
        )


class InvalidProjectArchiveError(ProjectFileError):
    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(
            f"'{path.name}' isn't a valid 3MF file ({detail})."
        )


class SliceMetadataError(PrintManagerError):
    """Base class for problems found once the file is confirmed to be a real 3MF."""


class SliceMetadataNotFoundError(SliceMetadataError):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f"'{path.name}' doesn't contain sliced print data. Make sure you exported it "
            "after slicing (not just saved the project) using Bambu Studio or OrcaSlicer."
        )


class SliceMetadataParseError(SliceMetadataError):
    def __init__(self, path: Path, detail: str) -> None:
        self.path = path
        self.detail = detail
        super().__init__(
            f"'{path.name}' has sliced data, but it couldn't be read: {detail}. "
            "The file may be from an unsupported slicer version."
        )
