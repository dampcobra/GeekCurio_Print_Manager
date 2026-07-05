import sqlite3

SCHEMA_VERSION = 1


def initialise_database(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS _meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quotes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_ref           TEXT    UNIQUE,
            created_at          TEXT    NOT NULL,
            source_file         TEXT    NOT NULL,
            slicer              TEXT    NOT NULL,
            profile_name        TEXT    NOT NULL,
            profile_label       TEXT    NOT NULL,
            print_time_s        INTEGER NOT NULL,
            total_weight_g      REAL    NOT NULL,
            print_time_cost     TEXT    NOT NULL,
            material_cost       TEXT    NOT NULL,
            overhead_multiplier TEXT    NOT NULL,
            markup_percentage   TEXT    NOT NULL,
            subtotal            TEXT    NOT NULL,
            markup_amount       TEXT    NOT NULL,
            total               TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quote_plates (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id         INTEGER NOT NULL REFERENCES quotes(id),
            plate_index      INTEGER NOT NULL,
            print_time_s     INTEGER NOT NULL,
            weight_g         REAL    NOT NULL,
            support_used     INTEGER,
            printer_model_id TEXT
        );

        CREATE TABLE IF NOT EXISTS quote_plate_filaments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id    INTEGER NOT NULL REFERENCES quote_plates(id),
            filament_id INTEGER NOT NULL,
            type        TEXT    NOT NULL,
            color       TEXT,
            used_g      REAL    NOT NULL,
            used_m      REAL
        );
    """)
    # executescript auto-commits; insert version marker separately
    conn.execute(
        "INSERT OR IGNORE INTO _meta (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()
