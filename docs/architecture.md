# Architecture

## Why a `src` layout

The importable package (`src/geekcurio_print_manager/`) is kept separate from the repository root.
This prevents accidentally importing the package from the working directory instead of the
installed copy, which is a common source of "works on my machine" bugs in Python projects. `pip
install -e .` (backed by the `pyproject.toml` in this repo) makes the package importable everywhere
without `sys.path` hacks.

## Why separate packages instead of one big module

Each package has exactly one reason to change:

- **`models/`** — pure data. No file I/O, no parsing, no UI. This is the shared vocabulary every
  other package speaks. `PrintJob` / `PlateSummary` / `FilamentUsage` describe a parsed 3MF project;
  totals are computed properties so they can never drift. `PricingConfig` (Milestone 2) holds
  pricing rules with sensible defaults. `QuoteBreakdown` (Milestone 2) is the immutable result of a
  quote calculation, carrying every line-item needed to render a quote in any UI.
  `PricingProfile` (Milestone 2.1) is a named wrapper around a `PricingConfig` — it adds a
  machine-readable `name` and a human-readable `label` so UIs can present and store profiles by
  name without `PricingConfig` itself needing to know it has one. The five built-in profiles live as
  a module-level tuple in `models/pricing_profile.py`; `QuoteService` deliberately remains unaware
  of profiles and continues to accept a bare `PricingConfig` — profile selection is the caller's
  responsibility. All monetary fields in `PricingConfig` and `QuoteBreakdown` use `decimal.Decimal`
  (Milestone 2.2); non-monetary measurements such as print time in seconds and material weight in
  grams remain plain numeric types. Decimal values are always constructed from strings
  (`Decimal("0.05")`), never from floats. Conversion from float measurements happens at the
  calculation boundary in `QuoteService` using `str()` to avoid binary float representation issues.
  Each monetary output field is quantized to `Decimal("0.01")` with `ROUND_HALF_UP`.
  `SavedQuote` (Milestone 3) is a persisted snapshot combining a `QuoteBreakdown`, the full
  `PlateSummary` tuple from the originating `PrintJob`, and metadata: a professional quote
  reference (`GCQ-YYYY-NNNNNN`), creation timestamp, source filename, slicer, and snapshotted
  profile name and label. Once saved, a `SavedQuote` is immutable — it reflects exactly what was
  quoted regardless of any later changes to pricing profiles.
- **`parsers/`** — everything that knows the *shape* of a specific slicer's output. Today there's
  one implementation, `bambu_orca.py`, targeting Bambu Studio and OrcaSlicer (they share an
  identical `Metadata/slice_info.config` format because OrcaSlicer's 3MF reader/writer was forked
  directly from Bambu Studio's). All parsers implement the small `SlicerProjectParser` interface in
  `base.py` (`can_parse`, `parse`), so adding support for a different slicer later means writing one
  new file and registering it with `InspectionService` — nothing else changes.
- **`services/`** — the seam between "raw file" and "the rest of the app." `InspectionService` is
  the only thing that knows how to go from a file path to a validated `PrintJob`: it checks the file
  exists, confirms it's a genuine 3MF archive *before* looking for slicer-specific metadata (so a
  corrupted or unrelated zip fails with "not a valid 3MF" rather than a confusing "missing metadata"
  message), then hands off to whichever registered parser recognises the archive. `QuoteService`
  (Milestone 2) accepts a `PrintJob` and a `PricingConfig` and returns a `QuoteBreakdown` — it has
  no knowledge of 3MF files, parsers, or archives. `QuoteRepository` (Milestone 3) persists and
  retrieves `SavedQuote` records via a SQLite connection. It accepts an already-initialised
  `sqlite3.Connection` so callers (the CLI entry point, or tests using in-memory databases) control
  the connection lifecycle independently of the service logic.
- **`db/`** — database infrastructure only; no business logic. `database.py` resolves the database
  path via `platformdirs` (writing to `%LOCALAPPDATA%\GeekCurio\GCPM\gcpm.sqlite` on Windows),
  creates the application data directory on first run, and provides an `open_connection` factory
  that sets `PRAGMA foreign_keys = ON` and `row_factory = sqlite3.Row`. `schema.py` declares all
  `CREATE TABLE IF NOT EXISTS` statements and a `_meta` table carrying a `schema_version` integer
  so future migrations can determine what they are upgrading from. Calling `initialise_database`
  twice is safe — all statements are idempotent.
- **`exporters/`** — turns model objects into external representations. `text_export.py` formats a
  `PrintJob` as TXT/CSV. `quote_export.py` (Milestone 2) formats a `PrintJob` + `QuoteBreakdown`
  as a human-readable quote report; it accepts an optional `quote_ref` so the assigned reference
  number appears in the output after a quote is saved. Neither exporter knows how the job was
  obtained. Milestone 4's PDF export will be a new file in this package alongside both.
- **`ui/`** — presentation only. `console.py` is Milestone 1's entire interface: read a path, call
  the service, print the result or the error. It contains no business logic, so when Phase 3
  introduces PySide6, the GUI becomes a new `ui/qt/` subpackage that calls the exact same
  `InspectionService` — the console UI keeps working unchanged alongside it.
- **`utils/`** — small, stateless helpers with no dependencies on the rest of the app
  (`formatting.py` for display strings, `archive.py` for safe zip handling), reused wherever needed
  without creating coupling between packages.

## Why a typed exception hierarchy

The brief requires the app to "fail gracefully with clear error messages." A flat `except
Exception` swallows real bugs alongside expected failure modes and gives users unhelpful messages.
Instead, `exceptions.py` defines two shallow trees:

- `ProjectFileError` — something's wrong with the file itself (doesn't exist, isn't a valid 3MF
  archive) — discovered *before* we assume anything about its contents.
- `SliceMetadataError` — the file is a genuine 3MF, but the sliced print data we need is missing or
  unreadable (most commonly: the project was saved but never actually sliced/exported).

Every concrete exception builds its own human-readable message from the offending path in its
constructor, so `ui/console.py` never constructs error text itself — it just prints `str(exc)`.
This also means a future GUI can catch the same exceptions and show them in a dialog instead of a
terminal line, with no changes to `services/` or `parsers/`.

## Extension points for later milestones

- **Milestone 4 (PDF quotes)** — add `exporters/pdf_export.py`. It will consume `SavedQuote`
  records retrieved via `QuoteRepository.get_by_ref()`, so the PDF always reflects the exact data
  that was stored — not a transient recalculation. Per-plate detail is already persisted in
  `quote_plates` / `quote_plate_filaments` ready for use.
- **Milestone 5 (GUI)** — a `ui/qt/` subpackage calling the same `InspectionService`,
  `QuoteService`, and `QuoteRepository` the console already uses. The console CLI keeps working
  unchanged alongside it.
- **Future (Customers, Orders, Inventory)** — new service and model files. `QuoteRepository` can
  gain a `customer_id` foreign key when the customers table exists; no changes to existing columns
  required. `PrintJob.filament_totals_by_material()` is the natural integration point for inventory
  decrements when a print is queued.

## Deliberately not built yet

No parser registry/plugin framework, no abstract factory, no settings/config system, no logging
framework. With exactly one slicer parser and one console UI, those would be speculative complexity
with no current caller. `SlicerProjectParser` gives just enough abstraction to add a second parser
without a rewrite; nothing more is justified until there's a second one to add.

## Known technical debt

No current known debt in the money layer. The float-to-Decimal migration was completed in
Milestone 2.2. If a future requirement calls for banker's rounding or a different quantization
strategy, that is a one-line change to the `_PENNY` constant and rounding mode in
`services/quote_service.py`.
