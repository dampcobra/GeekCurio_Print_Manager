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
