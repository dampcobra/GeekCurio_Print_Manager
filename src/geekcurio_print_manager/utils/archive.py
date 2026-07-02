import zipfile
from pathlib import Path
from typing import BinaryIO

from geekcurio_print_manager.exceptions import InvalidProjectArchiveError

REQUIRED_3MF_ENTRIES = ("[Content_Types].xml", "3D/3dmodel.model")


def open_archive(source: Path | BinaryIO, *, display_path: Path) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise InvalidProjectArchiveError(display_path, "the archive could not be opened") from exc


def ensure_3mf_skeleton(archive: zipfile.ZipFile, *, display_path: Path) -> None:
    names = set(archive.namelist())
    missing = [entry for entry in REQUIRED_3MF_ENTRIES if entry not in names]
    if missing:
        raise InvalidProjectArchiveError(
            display_path, f"missing required 3MF entries: {', '.join(missing)}"
        )
