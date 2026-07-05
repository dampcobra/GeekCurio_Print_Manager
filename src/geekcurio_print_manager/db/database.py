import sqlite3
from pathlib import Path

from platformdirs import user_data_dir


def get_db_path() -> Path:
    data_dir = Path(user_data_dir("GCPM", "GeekCurio"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "gcpm.sqlite"


def open_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path if db_path is not None else get_db_path()
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
