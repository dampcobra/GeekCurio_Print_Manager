import sqlite3

from geekcurio_print_manager.db.schema import SCHEMA_VERSION, initialise_database


def _fresh() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def test_schema_creates_all_tables():
    conn = _fresh()
    initialise_database(conn)
    tables = {row["name"] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "_meta" in tables
    assert "quotes" in tables
    assert "quote_plates" in tables
    assert "quote_plate_filaments" in tables


def test_schema_version_is_written():
    conn = _fresh()
    initialise_database(conn)
    row = conn.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
    assert row is not None
    assert int(row["value"]) == SCHEMA_VERSION


def test_schema_is_idempotent():
    conn = _fresh()
    initialise_database(conn)
    initialise_database(conn)  # second call must not raise or duplicate the version row
    rows = conn.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchall()
    assert len(rows) == 1


def test_notes_column_exists_in_quotes_table():
    conn = _fresh()
    initialise_database(conn)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "notes" in cols


def test_migration_adds_notes_column_to_v1_schema():
    conn = _fresh()
    # Build a v1 schema by hand — no notes column, schema_version = 1
    conn.executescript("""
        CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, quote_ref TEXT UNIQUE,
            created_at TEXT NOT NULL, source_file TEXT NOT NULL,
            slicer TEXT NOT NULL, profile_name TEXT NOT NULL, profile_label TEXT NOT NULL,
            print_time_s INTEGER NOT NULL, total_weight_g REAL NOT NULL,
            print_time_cost TEXT NOT NULL, material_cost TEXT NOT NULL,
            overhead_multiplier TEXT NOT NULL, markup_percentage TEXT NOT NULL,
            subtotal TEXT NOT NULL, markup_amount TEXT NOT NULL, total TEXT NOT NULL
        );
        CREATE TABLE quote_plates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL REFERENCES quotes(id),
            plate_index INTEGER NOT NULL, print_time_s INTEGER NOT NULL,
            weight_g REAL NOT NULL, support_used INTEGER, printer_model_id TEXT
        );
        CREATE TABLE quote_plate_filaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id INTEGER NOT NULL REFERENCES quote_plates(id),
            filament_id INTEGER NOT NULL, type TEXT NOT NULL,
            color TEXT, used_g REAL NOT NULL, used_m REAL
        );
    """)
    conn.execute("INSERT INTO _meta (key, value) VALUES ('schema_version', '1')")
    conn.commit()

    cols_before = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "notes" not in cols_before

    initialise_database(conn)

    cols_after = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "notes" in cols_after
    row = conn.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
    assert int(row["value"]) == SCHEMA_VERSION


def test_customer_name_column_exists_in_quotes_table():
    conn = _fresh()
    initialise_database(conn)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "customer_name" in cols


def test_project_name_column_exists_in_quotes_table():
    conn = _fresh()
    initialise_database(conn)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "project_name" in cols


def test_migration_adds_customer_and_project_name_columns_to_v2_schema():
    conn = _fresh()
    # Build a v2 schema by hand — notes present but no customer_name/project_name
    conn.executescript("""
        CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, quote_ref TEXT UNIQUE,
            created_at TEXT NOT NULL, source_file TEXT NOT NULL,
            slicer TEXT NOT NULL, profile_name TEXT NOT NULL, profile_label TEXT NOT NULL,
            print_time_s INTEGER NOT NULL, total_weight_g REAL NOT NULL,
            print_time_cost TEXT NOT NULL, material_cost TEXT NOT NULL,
            overhead_multiplier TEXT NOT NULL, markup_percentage TEXT NOT NULL,
            subtotal TEXT NOT NULL, markup_amount TEXT NOT NULL, total TEXT NOT NULL,
            notes TEXT
        );
        CREATE TABLE quote_plates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL REFERENCES quotes(id),
            plate_index INTEGER NOT NULL, print_time_s INTEGER NOT NULL,
            weight_g REAL NOT NULL, support_used INTEGER, printer_model_id TEXT
        );
        CREATE TABLE quote_plate_filaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_id INTEGER NOT NULL REFERENCES quote_plates(id),
            filament_id INTEGER NOT NULL, type TEXT NOT NULL,
            color TEXT, used_g REAL NOT NULL, used_m REAL
        );
    """)
    conn.execute("INSERT INTO _meta (key, value) VALUES ('schema_version', '2')")
    conn.commit()

    cols_before = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "customer_name" not in cols_before
    assert "project_name" not in cols_before

    initialise_database(conn)

    cols_after = {r["name"] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
    assert "customer_name" in cols_after
    assert "project_name" in cols_after
    row = conn.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
    assert int(row["value"]) == SCHEMA_VERSION


def test_quotes_table_has_autoincrement_id():
    conn = _fresh()
    initialise_database(conn)
    conn.execute(
        """
        INSERT INTO quotes (
            quote_ref, created_at, source_file, slicer,
            profile_name, profile_label,
            print_time_s, total_weight_g,
            print_time_cost, material_cost, overhead_multiplier,
            markup_percentage, subtotal, markup_amount, total
        ) VALUES ('GCQ-2026-000001', '2026-07-05T12:00:00Z', 'test.3mf', 'BambuStudio',
                  'fdm_pla', 'FDM - PLA', 3600, 50.0,
                  '3.00', '2.50', '1.0', '0', '5.50', '0.00', '5.50')
        """
    )
    conn.commit()
    row = conn.execute("SELECT id FROM quotes WHERE quote_ref = 'GCQ-2026-000001'").fetchone()
    assert row["id"] == 1
