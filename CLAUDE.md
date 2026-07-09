# GeekCurio Print Manager — Project Reference

> **This document is the single source of truth for any developer or AI assistant working on this project.**
> It describes not just what the code does, but why it was designed this way.
> Keeping this file accurate is part of the Definition of Done for every significant change.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Design Principles](#2-core-design-principles)
3. [Architecture](#3-architecture)
4. [Data Model](#4-data-model)
5. [Coding Standards](#5-coding-standards)
6. [AI Collaboration Rules](#6-ai-collaboration-rules)
7. [Development Workflow](#7-development-workflow)
8. [Current Roadmap](#8-current-roadmap)
9. [Lessons Learned](#9-lessons-learned)
10. [Future Ideas](#10-future-ideas)
11. [Known Technical Debt](#11-known-technical-debt)
12. [Development Philosophy](#12-development-philosophy)

---

## 1. Project Overview

### What GCPM Is

GeekCurio Print Manager (GCPM) is a desktop business tool for GeekCurio, a UK-based 3D printing studio that produces premium tabletop gaming accessories. It automates the process of turning a slicer project file into a professional customer quotation.

The core workflow is:

```
.3mf project file → parse print metadata → calculate quote → save to database → export customer PDF
```

Today this workflow is entirely CLI-driven. The architecture is explicitly designed to be lifted into a PySide6 desktop GUI in a future phase without changing the service or data layer.

### Business Goals

- Eliminate manual quote calculation, which is error-prone and inconsistent.
- Produce professional, brand-consistent PDF quotations that can be sent to customers without further editing.
- Maintain a persistent quote log that provides a basic audit trail.
- Keep internal pricing information (markup, overhead, per-gram rates) completely hidden from customer-facing documents.
- Give the business owner confidence that quotes are arithmetically correct and reproducible.

### Target Users

**Primary**: The business owner (sole operator at present), running the tool on their own Windows workstation.

**Secondary**: Any future employee or collaborator who needs to generate quotes or inspect print jobs.

The tool is not a customer-facing product. It is an internal business operations tool.

### Long-Term Vision

GCPM is the first layer of a broader operational platform. Future phases include:

- **Phase 2** (current CLI foundation): Service layer complete, quote persistence, PDF export.
- **Phase 3**: PySide6 desktop GUI — all business logic reused unchanged.
- **Phase 4+**: Packing list generation, print queue management, material inventory tracking, customer order history.

The CLI is a means to an end. Every architectural decision in the service and data layers has been made with the GUI phase in mind.

### Current Milestone

**Milestone 4.2 is complete.** The full quote-to-PDF pipeline is operational via CLI, including optional customer and project display names. See [Section 8](#8-current-roadmap) for the full roadmap.

---

## 2. Core Design Principles

These principles are not suggestions. They reflect deliberate decisions made during development and should not be reversed without explicit discussion.

### 2.1 Simplicity Over Cleverness

Every module does one thing and does it plainly. Prefer an extra function over a clever abstraction. Prefer a readable `if/elif` chain over a metaprogramming shortcut. The next person reading this code may be unfamiliar with the domain — clarity is a feature.

### 2.2 The Service Layer Must Remain UI-Agnostic

`services/`, `models/`, `parsers/`, `db/`, and `exporters/` must contain zero UI code and zero knowledge of how they are invoked. They accept typed Python objects and return typed Python objects. The CLI (`ui/`, `app.py`) is a thin wrapper. When the GUI arrives, these layers are reused without modification.

### 2.3 Decimal Arithmetic for All Money

Every monetary value in the system is a `decimal.Decimal`. Python `float` is never used for prices, costs, or totals — anywhere. The float-to-Decimal boundary is crossed exactly once, inside `QuoteService.calculate()`, using `str()` conversion to avoid binary representation contamination. All monetary outputs are quantized to the penny using `ROUND_HALF_UP`.

This is non-negotiable. Floats accumulate rounding errors. A quote that is wrong by a penny is a bug.

### 2.4 SQLite Is the Operational Database

Quote history lives in a single SQLite file at `%LOCALAPPDATA%\GeekCurio\GCPM\gcpm.sqlite`. No external database server. No ORM. No cloud sync. The file is local, portable, and zero-configuration. It can be backed up by simply copying the file.

### 2.5 Snapshots, Not References

When a quote is saved, all pricing parameters — hourly rate, per-gram rate, overhead multiplier, markup percentage, profile name, profile label — are written into the `quotes` table row. If built-in profiles are changed in a future version, existing saved quotes are unaffected. A quote is a snapshot of what was calculated at that moment, not a pointer to current configuration.

### 2.6 Customer Documents Must Never Expose Internal Calculations

The customer PDF shows the total cost and the project name. It does not show markup percentages, overhead multipliers, profile names, hourly machine rates, or per-gram material rates. This is enforced by the PDF exporter, verified by tests, and must never change without explicit agreement from the business owner.

### 2.7 Extensibility at the Parser Layer, Nowhere Else

The `SlicerProjectParser` ABC exists because a second slicer format (e.g. PrusaSlicer, Cura) may need to be supported in future. Adding a new parser requires one new file and one registration call — no changes to the service, model, or CLI layers.

Extensibility is designed in where the problem domain genuinely requires it (slicer formats). It is deliberately absent elsewhere (there is no plugin system, no hooks, no event bus).

### 2.8 No Speculative Complexity

No feature should be implemented until it is needed for a concrete milestone. No abstraction should be introduced because it might be useful later. No backwards-compatibility shim should be added unless a concrete backward-compatibility requirement exists. Delete things when they are no longer needed.

### 2.9 Prefer Maintainability Over Premature Optimisation

This is a single-user desktop tool. Performance is not a concern at any current scale. Readable code that runs in 200ms is better than clever code that runs in 20ms.

### 2.10 AI Should Assist the Business Owner, Not Replace Their Judgment

No automated pricing decision should be taken without user confirmation. The tool calculates; the human reviews and decides. Future features (price suggestions, smart defaults, historical comparisons) should always surface information to the user — they should never act autonomously on pricing.

---

## 3. Architecture

### 3.1 Overview

GCPM is a layered Python application using a `src/` package layout. The layers, from innermost to outermost, are:

```
models/          — pure data structures (dataclasses, no I/O)
parsers/         — slicer file reading (one ABC, one concrete implementation)
services/        — business logic (inspection, calculation, persistence)
db/              — database infrastructure (schema, migration, connection)
exporters/       — output generation (text, CSV, PDF)
ui/              — presentation (CLI argument parsing, output formatting)
app.py           — entry points wiring layers together
```

Dependencies flow inward. `ui/` knows about `services/` and `exporters/`. `services/` knows about `models/` and `parsers/`. Nothing in `models/` imports from any other layer.

### 3.2 Repository Layout

```
GeekCurio_Print_Manager/
├── CLAUDE.md                           ← this file
├── README.md                           ← setup and CLI usage
├── pyproject.toml                      ← package metadata, entry points, build config
├── requirements.txt                    ← runtime deps (includes PySide6 for future M5)
├── requirements-dev.txt                ← dev deps (pytest, pypdf)
├── docs/
│   └── architecture.md                 ← extended design rationale
├── Sample Projects/                    ← gitignored; local .3mf files for manual testing
├── src/geekcurio_print_manager/
│   ├── __init__.py                     ← package version (__version__ = "0.1.0")
│   ├── __main__.py                     ← python -m entry point
│   ├── app.py                          ← three CLI entry point functions
│   ├── exceptions.py                   ← typed exception hierarchy
│   ├── assets/branding/
│   │   └── geekcurio-logo.png          ← bundled brand asset; loaded via importlib.resources
│   ├── models/
│   │   ├── print_job.py                ← PrintJob, PlateSummary, FilamentUsage
│   │   ├── pricing_config.py           ← PricingConfig (frozen dataclass, Decimal fields)
│   │   ├── pricing_profile.py          ← PricingProfile, BUILTIN_PROFILES, get_profile()
│   │   ├── quote.py                    ← QuoteBreakdown (frozen dataclass, Decimal fields)
│   │   └── saved_quote.py             ← SavedQuote (frozen snapshot of a persisted quote)
│   ├── parsers/
│   │   ├── base.py                     ← SlicerProjectParser ABC
│   │   └── bambu_orca.py              ← BambuOrcaParser (Bambu Studio / OrcaSlicer)
│   ├── services/
│   │   ├── inspection_service.py       ← InspectionService: path → PrintJob
│   │   ├── quote_service.py            ← QuoteService: PrintJob + PricingConfig → QuoteBreakdown
│   │   └── quote_repository.py        ← QuoteRepository: save / get_by_ref / list_recent
│   ├── db/
│   │   ├── database.py                 ← get_db_path(), open_connection()
│   │   └── schema.py                  ← initialise_database(), migration logic, SCHEMA_VERSION
│   ├── exporters/
│   │   ├── text_export.py             ← text report and CSV generation
│   │   ├── quote_export.py            ← terminal quote display
│   │   └── pdf_quote_export.py        ← customer-facing PDF (fpdf2)
│   ├── ui/
│   │   ├── console.py                 ← M1 inspector console (run())
│   │   ├── quote_console.py           ← M2/M3 quote + save console (run_quote())
│   │   └── pdf_quote_console.py       ← M4 PDF generation console (run_pdf_quote())
│   └── utils/
│       ├── archive.py                 ← open_archive(), ensure_3mf_skeleton()
│       └── formatting.py             ← display_project_name(), format_duration(), format_weight()
└── tests/
    ├── conftest.py                    ← shared pytest fixtures
    ├── fixtures/slice_info_builder.py ← build_fake_3mf() in-memory archive factory
    ├── db/test_schema.py
    ├── exporters/
    │   ├── test_pdf_quote_export.py
    │   ├── test_quote_export.py
    │   └── test_text_export.py
    ├── models/
    │   ├── test_pricing_config.py
    │   ├── test_pricing_profile.py
    │   └── test_print_job.py
    ├── parsers/test_bambu_orca_parser.py
    ├── services/
    │   ├── test_inspection_service.py
    │   ├── test_quote_repository.py
    │   └── test_quote_service.py
    └── ui/test_pdf_quote_console.py
```

### 3.3 Entry Points

Three CLI commands are registered in `pyproject.toml`:

| Command | Handler | Purpose |
|---|---|---|
| `geekcurio-print-manager` | `app:main` | Inspect a `.3mf` file; optionally export TXT / CSV |
| `geekcurio-quote` | `app:quote_main` | Generate and save a quote; supports pricing profiles |
| `geekcurio-quote-pdf` | `app:pdf_quote_main` | Generate a customer PDF from a saved quote reference |

`python -m geekcurio_print_manager` also resolves to `app:main` via `__main__.py`.

### 3.4 Module Responsibilities

**`models/`** — Pure data. No I/O, no parsing, no business logic. Defines the shared vocabulary used by all other layers. All dataclasses are `frozen=True, slots=True`.

**`parsers/`** — Slicer-specific file reading only. The `SlicerProjectParser` ABC requires two methods: `can_parse(archive)` and `parse(archive, source_path)`. The `BambuOrcaParser` reads `Metadata/slice_info.config` (an XML file inside the `.3mf` zip). OrcaSlicer uses an identical format to Bambu Studio because OrcaSlicer was forked from it.

**`services/`** — Business logic with no I/O dependencies.
- `InspectionService`: validates the file path, opens the zip, checks the 3MF skeleton, delegates to the first matching parser.
- `QuoteService`: converts measurements to `Decimal` at the boundary, applies rates and multipliers, quantizes results.
- `QuoteRepository`: persists quotes and their plate/filament detail; generates the `GCQ-YYYY-NNNNNN` reference; reconstructs `SavedQuote` objects from database rows.

**`db/`** — Infrastructure only. No business logic. Owns the database path resolution, connection creation, schema creation, and migration. Does not make business decisions about data.

**`exporters/`** — Transforms model objects into output representations. Has no knowledge of where the models came from or how to obtain them.

**`ui/`** — Thin presentation layer. Parses CLI arguments, calls services, prints results. All error handling at this layer catches `PrintManagerError` and prints `str(exc)`. No business logic lives here.

**`utils/`** — Stateless helpers with no application dependencies. Safe to import from any layer.

### 3.5 Data Flow

#### Inspection (M1)

```
argv[1] (file path)
  → InspectionService.inspect(path)
      → Path.is_file()                      → ProjectFileNotFoundError if missing
      → open_archive(path)                  → InvalidProjectArchiveError if bad zip
      → ensure_3mf_skeleton(archive)        → InvalidProjectArchiveError if not 3MF
      → BambuOrcaParser.can_parse(archive)
      → BambuOrcaParser.parse(archive, path)
          → reads Metadata/slice_info.config (XML)
          → builds FilamentUsage tuples per plate
          → builds PlateSummary tuples
          → returns PrintJob
  → build_text_report(job) → stdout
```

#### Quote Generation and Save (M2/M3)

```
argv (path, profile name)
  → get_profile(name)                       → PricingProfile
  → InspectionService.inspect(path)         → PrintJob
  → QuoteService(config).calculate(job)
      → hours = Decimal(total_time_s) / 3600
      → weight = Decimal(str(total_weight_g))   ← str() avoids float binary repr
      → time_cost = hours * hourly_machine_rate
      → material_cost = weight * material_cost_per_gram
      → subtotal = (time_cost + material_cost) * overhead_multiplier
      → markup_amount = subtotal * (markup_pct / 100)
      → total = subtotal + markup_amount
      → all monetary fields quantized to Decimal("0.01") with ROUND_HALF_UP
      → returns QuoteBreakdown
  → QuoteRepository.save(conn, job, breakdown, profile)
      → INSERT quotes (quote_ref = NULL)
      → quote_ref = f"GCQ-{year}-{lastrowid:06d}"
      → UPDATE quotes SET quote_ref = ...
      → INSERT quote_plates (one per plate)
      → INSERT quote_plate_filaments (one per filament per plate)
      → conn.commit()
      → returns SavedQuote
  → build_quote_report(...) → stdout
```

#### PDF Export (M4)

```
argv (quote_ref, optional output path)
  → QuoteRepository.get_by_ref(conn, ref)
      → SELECT quotes + quote_plates + quote_plate_filaments
      → reconstructs Decimal values from TEXT columns
      → reconstructs plate and filament hierarchy
      → returns SavedQuote
  → build_pdf_quote(saved_quote, output_path)
      → _load_logo_bytes()    ← importlib.resources, graceful fallback if missing
      → _allocate_plate_costs()  ← proportional split; last plate absorbs remainder
      → renders: logo, title, metadata, tagline, intro, summary table,
                 plate breakdown, (multi-plate: recommendation), notes, closing
      → pdf.output(str(output_path))
```

### 3.6 Exception Hierarchy

```
PrintManagerError                              — base; never raised directly
├── ProjectFileError                           — file-level problems
│   ├── ProjectFileNotFoundError(path)
│   └── InvalidProjectArchiveError(path, detail)
└── SliceMetadataError                         — valid 3MF, data is missing or broken
    ├── SliceMetadataNotFoundError(path)       — no parser matched (file not sliced)
    └── SliceMetadataParseError(path, detail)  — parser matched but data is corrupt
```

Each exception constructs its user-facing message in `__init__`. UI layers catch `PrintManagerError` and print `str(exc)`. Exit code `0` = success, `1` = any error.

---

## 4. Data Model

### 4.1 Python Data Structures

All domain types are `frozen=True, slots=True` dataclasses. Immutability is enforced at the type level — no accidental mutation.

**`FilamentUsage`** — a single filament used on a single plate.
- `filament_id: int`, `type: str`, `used_g: float`, `color: str | None`, `used_m: float | None`

**`PlateSummary`** — one build plate from a multi-plate job.
- `index: int`, `print_time_s: int`, `weight_g: float`, `filaments: tuple[FilamentUsage, ...]`
- `support_used: bool | None`, `printer_model_id: str | None`

**`PrintJob`** — the complete parsed result from one `.3mf` file.
- `source_path: Path`, `slicer: str`, `plates: tuple[PlateSummary, ...]`
- Computed: `total_print_time_s`, `total_weight_g`
- Method: `filament_totals_by_material() → dict[tuple[str, str | None], float]`

**`PricingConfig`** — pricing parameters (all `Decimal`).
- `hourly_machine_rate: Decimal = Decimal("3.00")` (£/hour)
- `material_cost_per_gram: Decimal = Decimal("0.05")` (£/gram)
- `overhead_multiplier: Decimal = Decimal("1.0")` (neutral default)
- `markup_percentage: Decimal = Decimal("0")` (no markup by default)

**`PricingProfile`** — a named configuration preset.
- `name: str` (machine identifier, e.g. `fdm_pla`), `label: str` (human label), `config: PricingConfig`

**`QuoteBreakdown`** — the result of a quote calculation.
- Monetary fields: `print_time_cost`, `material_cost`, `overhead_multiplier`, `markup_percentage`, `subtotal`, `markup_amount`, `total` — all `Decimal`
- Measurement fields: `print_time_hours: float`, `material_weight_g: float` — native types

**`SavedQuote`** — a complete persisted quote, including a snapshot of all pricing parameters and the full plate hierarchy.
- `quote_ref: str` (e.g. `GCQ-2026-000001`), `created_at: str` (ISO 8601 UTC)
- `source_file: str` (filename only — no path; never mutated), `slicer: str`
- `profile_name: str`, `profile_label: str`
- `breakdown: QuoteBreakdown`, `plates: tuple[PlateSummary, ...]`
- `notes: str | None`
- `customer_name: str | None` — optional customer name shown on PDF; omitted from PDF if absent
- `project_name: str | None` — optional display name for PDF; falls back to cleaned `source_file` if absent

### 4.2 Built-in Pricing Profiles

Five profiles are defined as module-level constants in `models/pricing_profile.py`:

| `name` | `label` | Rate/hr | Rate/g | Markup |
|---|---|---|---|---|
| `fdm_pla` | FDM — PLA (Standard) | £3.00 | £0.05 | 0% |
| `fdm_petg` | FDM — PETG | £3.00 | £0.04 | 0% |
| `resin` | Resin | £4.00 | £0.15 | 0% |
| `premium_fdm` | Premium FDM / Custom Work | £3.00 | £0.05 | 30% |
| `internal_test` | Internal / Testing | £1.50 | £0.02 | 0% |

**Note on PLA vs PETG pricing:** PLA (£0.05/g) is priced higher than PETG (£0.04/g). This is intentional and reflects GeekCurio's actual supplier costs — PLA costs more per gram from their supplier than PETG. Do not "correct" this to the opposite without confirming current supplier pricing.

The resin profile's higher rates deliberately include cleanup time, IPA, support removal, and consumable overhead — not just machine exposure time.

`QuoteService` is given a `PricingConfig` directly and has no knowledge of profiles. Profile selection is always the caller's responsibility.

### 4.3 SQLite Schema

Current schema version: **3**. Stored in `_meta(key='schema_version')`.

```sql
CREATE TABLE IF NOT EXISTS _meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_ref           TEXT    UNIQUE,
    created_at          TEXT    NOT NULL,       -- ISO 8601 UTC
    source_file         TEXT    NOT NULL,       -- filename only, no directory path
    slicer              TEXT    NOT NULL,
    profile_name        TEXT    NOT NULL,
    profile_label       TEXT    NOT NULL,
    print_time_s        INTEGER NOT NULL,
    total_weight_g      REAL    NOT NULL,
    print_time_cost     TEXT    NOT NULL,       -- Decimal stored as string
    material_cost       TEXT    NOT NULL,
    overhead_multiplier TEXT    NOT NULL,
    markup_percentage   TEXT    NOT NULL,
    subtotal            TEXT    NOT NULL,
    markup_amount       TEXT    NOT NULL,
    total               TEXT    NOT NULL,
    notes               TEXT,                  -- nullable; added in schema v2
    customer_name       TEXT,                  -- nullable; added in schema v3
    project_name        TEXT                   -- nullable; added in schema v3
);

CREATE TABLE IF NOT EXISTS quote_plates (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id         INTEGER NOT NULL REFERENCES quotes(id),
    plate_index      INTEGER NOT NULL,
    print_time_s     INTEGER NOT NULL,
    weight_g         REAL    NOT NULL,
    support_used     INTEGER,                  -- 0/1/NULL
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
```

**Migration history**:
- v1 → v2: `ALTER TABLE quotes ADD COLUMN notes TEXT`
- v2 → v3: `ALTER TABLE quotes ADD COLUMN customer_name TEXT` and `ALTER TABLE quotes ADD COLUMN project_name TEXT`

### 4.4 Design Decisions: Database

- **Decimal as TEXT**: SQLite has no decimal type. All monetary values are stored as their string representation (e.g. `"6.75"`) and reconstructed via `Decimal(row["field"])`. This avoids any floating-point round-trip error.
- **AUTOINCREMENT as sequence counter**: The `quotes.id` integer primary key drives the quote reference number. Even if a row is deleted, the sequence does not reset. `GCQ-2026-000001` will always refer to the first quote inserted in 2026.
- **Quote ref two-step insert**: The ref cannot be generated before the row exists (we need `lastrowid`). The pattern is: INSERT with `quote_ref = NULL` → get `lastrowid` → UPDATE. This is the simplest correct approach.
- **Foreign keys enabled**: `PRAGMA foreign_keys = ON` is set on every connection. The plate and filament tables reference `quotes.id` with a real FK constraint.
- **Schema versioning**: The `_meta` table stores `schema_version` as a string. Migrations are run as numbered steps in `_migrate()`. Adding a migration = adding one `if current_version < N` block.

### 4.5 Backup Strategy

The database is a single file. Backup = copy the file. The recommended approach is to include `%LOCALAPPDATA%\GeekCurio\GCPM\gcpm.sqlite` in whatever backup solution the business owner uses for their workstation (e.g. Windows Backup, Backblaze, manual copy to Google Drive).

There is no automated backup or sync mechanism built into GCPM. This is intentional — see [Section 9.4](#94-why-google-drive-is-not-used-as-a-live-database).

---

## 5. Coding Standards

### 5.1 Naming Conventions

| Kind | Convention | Examples |
|---|---|---|
| Classes | `PascalCase` | `PrintJob`, `QuoteRepository`, `BambuOrcaParser` |
| Functions / methods | `snake_case` | `build_text_report`, `get_profile`, `open_archive` |
| Private / internal | Underscore prefix | `_parse_plate`, `_load_logo_bytes`, `_migrate` |
| Module constants | `UPPER_SNAKE` | `BUILTIN_PROFILES`, `SCHEMA_VERSION`, `CSV_HEADER` |
| Module-private constants | `_UPPER_SNAKE` | `_PENNY`, `_A4_W`, `_MARGIN`, `_C_BLACK` |
| CLI commands | kebab-case | `geekcurio-print-manager`, `geekcurio-quote-pdf` |
| Profile identifiers | underscore | `fdm_pla`, `fdm_petg`, `internal_test` |
| Quote references | `GCQ-YYYY-NNNNNN` | `GCQ-2026-000001` |
| Test files | `test_<module>.py` | `test_quote_repository.py` |

### 5.2 File and Folder Organisation

- Source code lives under `src/geekcurio_print_manager/`. The `src/` layout prevents accidental imports from the working directory and requires an editable install (`pip install -e .`).
- New business logic goes in the appropriate layer (`services/`, `models/`, etc.). If no existing layer fits, discuss before creating a new one.
- New exporters go in `exporters/`. A new slicer parser goes in `parsers/` (one file per slicer).
- Test files mirror the source layout: `tests/services/test_quote_service.py` tests `services/quote_service.py`.
- Assets bundled with the package go in `assets/`. Declare them in `pyproject.toml` under `[tool.setuptools.package-data]` and load them with `importlib.resources`.

### 5.3 Error Handling

- Raise typed exceptions from `exceptions.py` with human-readable messages built in the constructor. The UI layer should never construct an error message — it should only print `str(exc)`.
- Never swallow exceptions silently in business logic. If something goes wrong and you cannot handle it, let the exception propagate.
- The only place a broad `except Exception` is acceptable is for graceful degradation of optional non-critical features (e.g., the logo loading in `pdf_quote_export.py` — a missing logo should not crash a PDF generation).
- Do not add error handling for scenarios that cannot occur given correct internal usage. Trust internal contracts.

### 5.4 Comments and Documentation

- Default to writing no comments. Well-named identifiers are documentation.
- Add a comment only when the **why** is non-obvious: a hidden constraint, a workaround for a specific behaviour, or something that would surprise a future reader.
- Do not comment **what** the code does. Do not reference the current task, PR, or milestone number in code comments.
- Docstrings: one short line for public functions where the name alone is ambiguous. Never a multi-paragraph docstring.

### 5.5 Decimal Rules

- All monetary values must be `decimal.Decimal`. No exceptions.
- `float` → `Decimal` conversion: always via `str()`, never directly. Use `Decimal(str(float_value))`.
- `int` → `Decimal` conversion: direct is safe (`Decimal(integer_value)`).
- Quantize all monetary outputs to `Decimal("0.01")` with `ROUND_HALF_UP` before storing or displaying.
- Never store a `Decimal` in SQLite as a float column. Use `TEXT` and reconstruct with `Decimal(row["field"])`.

### 5.6 Testing

- Every piece of business logic must have tests.
- Tests use `pytest`. No test framework other than pytest.
- SQLite tests use `:memory:` databases — no filesystem I/O, no cleanup.
- `.3mf` fixtures use `build_fake_3mf()` from `tests/fixtures/slice_info_builder.py` — no real `.3mf` files in the test suite.
- PDF tests use `pypdf` to inspect PDF text content. Note: `pypdf` cannot reliably decode `£` from Helvetica WinAnsiEncoding, so tests assert on numeric amounts (e.g. `"6.75"`) rather than full currency strings (e.g. `"£6.75"`).
- A test that merely checks a function runs without crashing has marginal value. Assert on specific output values.
- When modifying functionality, update the relevant tests in the same commit. A failing test suite is not acceptable to merge.

### 5.7 Logging

There is currently no logging framework in this project. All user-facing output uses `print()`. This is deliberate at the current scale (see [Section 9.5](#95-no-logging-framework-yet)). If a logging framework is introduced, it should be introduced consistently and not mixed with ad-hoc `print()` calls.

### 5.8 Python Version

GCPM requires Python >= 3.13. Do not use compatibility shims for older Python versions. Features available in 3.13 (e.g. `slots=True` on dataclasses, `match` statements) are fair to use.

---

## 6. AI Collaboration Rules

These rules apply to any AI assistant working on this codebase.

### 6.1 Never Remove Working Functionality

Do not remove, disable, or refactor working code unless explicitly instructed to do so. If a cleanup or simplification is warranted, state it clearly and wait for confirmation before proceeding.

### 6.2 Prefer Small, Incremental Changes

Make the smallest change that achieves the goal. Do not restructure surrounding code as part of a bug fix. Do not refactor adjacent modules as part of a new feature. Limit the blast radius of every change.

### 6.3 Infer Intent from the Architecture

Before implementing anything, read the existing layer conventions. New code should feel like it was written by the same person as the existing code. Match naming patterns, structural patterns, and levels of abstraction.

### 6.4 Update This Document for Significant Changes

Update `CLAUDE.md` when a change is architecturally meaningful: a new module is introduced, the data model or schema changes, a dependency is added or removed, a CLI command changes, a pricing profile or rate is modified, a milestone is completed, or a design decision is made that future contributors need to understand.

Do not update `CLAUDE.md` for routine implementation work: small bug fixes, test additions that don't change behaviour, minor refactors within an existing module, or formatting changes. The document should evolve with the project's structure and intent — not log every commit.

### 6.5 Always Update Tests

If functionality changes, tests must change to reflect it. Do not leave tests that pass incorrectly or tests that are no longer testing what they claim to test.

### 6.6 Preserve Backwards Compatibility Where Practical

Do not change the SQLite schema without a migration. Do not change the `GCQ-YYYY-NNNNNN` reference format. Do not change CLI argument interfaces without flagging it as a breaking change.

### 6.7 Ask Before Making Breaking Database Changes

Any schema change must include a migration. Before writing a migration, confirm the approach with the project owner — especially `ALTER TABLE`, `DROP COLUMN`, or changes to the `quotes` table structure.

### 6.8 Do Not Invent Facts

If something about the business rules, pricing rationale, or roadmap is unclear, leave a `TODO` placeholder and note the ambiguity. Do not guess and present the guess as fact.

### 6.9 Explain Architectural Decisions

When introducing a pattern that is not already present in the codebase (a new design pattern, a new dependency, a new layer), explain why it was chosen and what the alternative was.

### 6.10 Keep the Customer PDF Clean

The PDF exporter is the most sensitive part of the application from a business perspective. Do not add any internal fields (markup, overhead, rates, profile name) to the PDF output. If there is any doubt about whether a field should appear in the customer PDF, the answer is: it should not.

### 6.11 Monetary Arithmetic Is Not Optional

Any code that touches pricing, costs, totals, or quote values must use `Decimal`. Suggesting or introducing `float` arithmetic for monetary values is not acceptable.

---

## 7. Development Workflow

### 7.1 Environment Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install package in editable mode (required for src/ layout)
pip install -e .

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 7.2 Running Tests

```powershell
pytest
```

All tests should pass before any commit. There are no known failing tests.

### 7.3 Branch Strategy

- `master` is the main branch and is always in a releasable state.
- Feature work is developed on named branches: `milestone/5-pyside6-gui`, `feature/packing-list`, `fix/pdf-font-encoding`.
- Commits are squashed or kept clean before merging to `master`. No "WIP" commits in history.

### 7.4 Commit Messages

- First line: short imperative summary (50 characters or fewer): `Add Milestone 4: PDF quote output from saved quote reference`
- No issue or ticket numbers in commit messages unless there is a formal tracking system.
- Commit message body (if needed) explains the why, not the what.

### 7.5 Milestones

Development is organised into milestones with clear scope. A milestone is not complete until:
- All planned functionality is implemented.
- All tests pass.
- The `CLAUDE.md` is updated to reflect any changes to architecture, data model, roadmap, or design decisions introduced by the milestone.
- The `README.md` reflects any new CLI commands or setup steps.

### 7.6 Definition of Done

A piece of work is done when:
- [ ] The functionality works correctly end-to-end.
- [ ] Tests are written or updated to cover the change.
- [ ] All tests pass.
- [ ] No new linting errors.
- [ ] `CLAUDE.md` is updated if the milestone, architecture, data model, pricing, or design decisions changed (not required for routine bug fixes or minor refactors).
- [ ] `README.md` is updated if the user-facing CLI or setup changed.

### 7.7 Manual Testing

Sample `.3mf` files are available in `Sample Projects/` (gitignored). These should be used to verify end-to-end behaviour after any change touching the parser, services, or PDF exporter. For PDF changes, visually inspect the generated PDF before committing.

---

## 8. Current Roadmap

### Completed Milestones

**Milestone 1 — 3MF Project Inspector**
- Parses Bambu Studio / OrcaSlicer `.3mf` files.
- Extracts per-plate print time and material weight.
- CLI: `geekcurio-print-manager <file.3mf>`
- Optional export to `.txt` and `.csv`.

**Milestone 2 — Quote Generator**
- `QuoteService` calculates cost from `PrintJob` + `PricingConfig`.
- `Decimal` arithmetic throughout; `ROUND_HALF_UP` quantisation.
- CLI: `geekcurio-quote <file.3mf> --profile fdm_pla`
- Five built-in pricing profiles.

**Milestone 2.1 — Pricing Profiles**
- `PricingProfile` model, `BUILTIN_PROFILES` tuple, `get_profile()` lookup.
- Profiles include: `fdm_pla`, `fdm_petg`, `resin`, `premium_fdm`, `internal_test`.

**Milestone 2.2 — Decimal Migration**
- All monetary fields migrated from `float` to `Decimal`.
- Float-to-Decimal boundary established at `QuoteService.calculate()` entry.

**Milestone 3 — Quote Persistence**
- SQLite database at `%LOCALAPPDATA%\GeekCurio\GCPM\gcpm.sqlite`.
- `QuoteRepository`: save, retrieve by ref, list recent.
- `GCQ-YYYY-NNNNNN` reference format.
- Schema migration infrastructure (v1 → v2 added `notes` field).

**Milestone 4 — PDF Quote Output**
- `build_pdf_quote()` using fpdf2.
- Customer-facing layout: logo, project summary, plate breakdown table, notes.
- Internal pricing information (markup, rates, profile) is never exposed.
- CLI: `geekcurio-quote-pdf GCQ-2026-000001`

**Milestone 4.1 — PDF Styling Refinement**
- GeekCurio brand logo embedded in PDF via `importlib.resources`.
- Professional A4 layout: section headings, proportional plate cost allocation, recommendation section for multi-plate jobs.
- Display name strips slicer extensions (`.gcode.3mf` → project name).

**Milestone 4.2 — Customer and Project Display Names**
- Optional `--customer` and `--project` CLI arguments on `geekcurio-quote`.
- `customer_name` and `project_name` stored on the `quotes` table (schema v3).
- PDF uses `project_name` if set; falls back to cleaned `source_file` display name.
- `Customer:` metadata line appears on PDF only when `customer_name` is provided.
- Blank and whitespace-only values normalised to `None` at the CLI layer.
- `source_file` is never mutated — original filename preserved for traceability.

### Current Milestone

**Milestone 4.2 is complete.** The project is in a stable, working state. The entire pipeline from `.3mf` file to customer PDF is operational via CLI, including optional customer and project display names.

### Upcoming Milestones

**Milestone 5 — PySide6 Desktop GUI**
- Replace the CLI with a native desktop window.
- All existing services, models, and exporters are reused without modification.
- UI screens: file picker, quote review, quote history, PDF export.
- `PySide6` is already in `requirements.txt`, waiting.

**Milestone 6 — Packing List Generator** *(planned)*
- Generate a packing list document from a saved quote.
- New exporter in `exporters/packing_list_export.py`.

**Milestone 7 — Material Inventory Tracking** *(planned)*
- Track filament spool inventory.
- Deduct material usage when a quote is marked as completed.

**Milestone 8 — Print Queue** *(planned)*
- Queue multiple jobs for a print run.
- Track status: queued → printing → complete → dispatched.

### Long-Term Goals

- A reliable, professional quoting and operations platform for a solo 3D printing business.
- The application should eliminate all manual calculation and all spreadsheet-based tracking.
- Customer communication should be entirely handled through GCPM-generated documents.
- Eventually: historical quote analytics, material cost tracking, profit margin reporting.

---

## 9. Lessons Learned

This section captures important decisions and the reasoning behind them. It should be updated whenever a significant decision is made.

### 9.1 Why SQLite Was Chosen

SQLite requires zero administration, zero network configuration, and zero running processes. For a single-user desktop application, it is the correct choice. It is battle-tested, produces a portable single file, and is directly supported by Python's standard library. The quote database will never have concurrent writers, so the limitations of SQLite do not apply.

PostgreSQL or any other server database would introduce deployment complexity with no benefit at this scale.

### 9.2 Why Decimal Arithmetic Was Introduced Mid-Project

The original M2 implementation used `float` for all monetary values. This was intentionally noted as technical debt and addressed in M2.2. The migration was triggered when edge-case testing revealed that float arithmetic produced totals that differed from the expected result by £0.01 in rare cases involving certain gram weights and time values.

The lesson: monetary arithmetic with `float` is always wrong. Use `Decimal` from the start. The migration in M2.2 is documented so this mistake is not repeated in future modules.

### 9.3 Why Customer PDFs Hide Markup

The PDF is sent to the customer as a quotation. The customer does not need to know the business's markup percentage, overhead multiplier, or internal rate structure. Exposing this information:
- Gives customers a basis for negotiation that undermines pricing integrity.
- Reveals the business's operational economics to competitors if a PDF is shared.
- Creates an unprofessional impression if internal labels (e.g. `fdm_pla`, `overhead_multiplier = 1.2`) appear in a customer document.

The PDF shows: project name, quote reference, date, total cost, plate breakdown, and notes. Nothing else. This is enforced by tests and must not change.

### 9.4 Why Google Drive Is Not Used as a Live Database

At an early planning stage, syncing the SQLite database to Google Drive was considered as a backup/portability mechanism. This was rejected because:
- Syncing a live SQLite file while it is being written can cause corruption.
- Google Drive's sync client is not designed for database files.
- The correct backup strategy is periodic file copy, not continuous sync.
- A future multi-device or multi-user scenario should use a proper server-based database, not a synced file.

If Google Drive integration is added in future, it should be for exporting completed documents (PDFs), not for the operational database.

### 9.5 No Logging Framework Yet

As of M4.1, there is no logging framework. All output is via `print()`. The rationale: with a single parser, a single UI mode, and a single developer, a logging framework would be speculative infrastructure. Adding it means deciding on log levels, handlers, formatters, and configuration — for a CLI tool that currently has one user.

When the GUI (M5) is built, the need for structured logging will become clearer. At that point, Python's `logging` module should be introduced consistently across all layers.

### 9.6 Why the src/ Layout Was Chosen

The `src/` layout prevents the package from being importable from the project root without installing it. This means tests always run against the installed package, not the working directory files. This catches import errors and missing `__init__.py` files that a flat layout would silently ignore. It requires `pip install -e .` after checkout — a small cost for a significant correctness guarantee.

### 9.7 Why Profiles Are Snapshotted at Save Time

When a quote is saved, `profile_name` and `profile_label` are written into the `quotes` row. If the built-in profiles are modified in a future version (different rates, new names), every historical quote retains the label that was shown to the customer. This preserves audit trail integrity. A quote that said "FDM — PLA (Standard)" must always say that, even if the standard PLA profile rates change next year.

### 9.8 The BambuOrcaParser Float-String Edge Case

OrcaSlicer and Bambu Studio occasionally write integer fields as float strings in `slice_info.config` — e.g. `print_time="4823.0"` rather than `print_time="4823"`. The parser's `_parse_int()` method converts via `float` first (`int(float(value))`) to handle this. A direct `int()` cast would raise a `ValueError` on the decimal string. This is a quirk of the slicer format, not a design choice.

### 9.9 The Quote Ref Two-Step Insert

The `GCQ-YYYY-NNNNNN` reference cannot be generated before the row exists — we need the SQLite `lastrowid` (the autoincrement integer) to build the string. The pattern is:
1. `INSERT INTO quotes (..., quote_ref, ...) VALUES (..., NULL, ...)`
2. Read `cursor.lastrowid`
3. Build `quote_ref = f"GCQ-{year}-{lastrowid:06d}"`
4. `UPDATE quotes SET quote_ref = ? WHERE id = ?`

This is slightly awkward but correct and simple. An alternative (generating a UUID) was considered but rejected — sequential human-readable references are more useful for a business than opaque UUIDs.

---

## 10. Future Ideas

These are not planned or committed. They are captured here so they are not forgotten.

- **Quote templates / quick notes**: Pre-defined note templates for common job types (standard FDM, rush order, multi-colour) that can be selected at quote time.
- **Email integration**: Generate a quote email draft from a saved quote and open the user's email client with it pre-populated.
- **Customer database**: Track customers by name and associate quotes with them.
- **Job costing vs. quote reconciliation**: After a job is complete, compare actual material used (from a completed print) against the quoted estimate.
- **Material cost tracking**: Maintain a materials inventory with actual purchase cost per gram rather than a fixed rate.
- **Quote PDF versioning**: Allow re-generating a quote PDF with updated notes or layout without changing the underlying quote data.
- **Quote status workflow**: Queued → Sent → Accepted / Rejected → In Progress → Complete → Dispatched.
- **Analytics dashboard**: Revenue by profile type, average job size, quote acceptance rate.
- **Multi-printer support**: Track which printer produced which job, with per-printer hourly rates.
- **Export to Google Sheets**: Export the quote log to a Sheets document for the business owner's accounting workflow.

---

## 11. Known Technical Debt

### 11.1 `requirements.txt` Contains PySide6 Prematurely

`PySide6` is listed in `requirements.txt` but not in `pyproject.toml` dependencies. It is unused until M5. A developer installing from `requirements.txt` will download a large dependency they do not yet need. This was left in place to signal the intent, but it creates a discrepancy between `requirements.txt` and `pyproject.toml`.

**Resolution**: Once M5 begins, add `PySide6` to `pyproject.toml` and remove the discrepancy.

### 11.2 Plate Cost Allocation Is a Heuristic

`_allocate_plate_costs()` splits the total cost proportionally by plate contribution to `print_time_cost + material_cost`, then scales by `total / base_sum` so that markup is distributed proportionally. The last plate absorbs the rounding remainder. This is mathematically sound but is a reasonable approximation — there is no guarantee that a plate's "fair share" of overhead maps cleanly to this split. For most practical jobs, the difference is pennies.

**Resolution**: This is acceptable for the current use case. If the business owner wants a different allocation strategy, it can be replaced.

### 11.3 No Logging

As noted in Section 9.5, there is no logging framework. `print()` is used throughout. This is adequate now but will become a problem when the GUI is introduced.

**Resolution**: Introduce `logging` at the start of M5, before any GUI code is written.

### 11.4 No Input Sanitisation on Notes Field

The `notes` field accepted by `QuoteRepository.save()` and rendered in the PDF is passed through without sanitisation. For the current single-user context this is fine. If the application ever accepts input from an untrusted source, this should be reviewed.

### 11.5 PDF Plate Description Is Hardcoded

The `Description` column in the plate breakdown table always reads `"Printed components"` and `Qty` always reads `"1"`. These are placeholder values that are correct for the current use case but will need to be configurable if GCPM is used for jobs that have a meaningful distinction between plate contents.

### 11.6 No Currency Localisation

Currency amounts are formatted as bare numbers with a hardcoded `£` prefix. The business is UK-based, so this is appropriate now. If GCPM is ever used for non-GBP quotes, the currency handling will need to be revisited throughout the exporters and data model.

### 11.7 Orphan PDF in Repository Root

`GCQ-2026-000002.pdf` exists in the working directory but is not committed or gitignored. It is a test artefact from manual testing. This should be added to `.gitignore` or deleted.

---

## 12. Development Philosophy

GCPM should be a pleasure to work on. That means:

**Reliability first.** The tool handles business-critical calculations. A wrong quote damages the business. Every pricing calculation must be correct, every time, for every input. Tests are not optional.

**Understand before you change.** Before modifying any module, read its tests. The tests describe the intended behaviour more precisely than the code. If you do not understand what a module does from its tests, read the module and then read the tests again.

**The architecture is load-bearing.** The layered design (models → services → ui) exists so that the GUI phase does not require rewriting the business logic. This constraint must be respected. Any change that couples a service to a CLI concern, or mixes business logic with presentation, is moving in the wrong direction.

**The project should grow, not sprawl.** Every new feature should have a clear home in the existing layer structure. If something does not fit cleanly, the question is whether the structure needs a new layer (unlikely) or whether the feature is being added at the wrong level of abstraction (more likely).

**Small codebase, big confidence.** A codebase that is thoroughly tested and well-understood is more valuable than a larger codebase that nobody is confident in. Prefer depth of coverage over breadth of features. It is better to have three features that work perfectly than six features where two of them have edge cases that nobody has tested.

**Write for the person who comes next.** That person may be a future collaborator, an AI assistant, or the current developer returning after six months. Write code that communicates its intent clearly. Update this document when the project changes. Leave the codebase better than you found it.
