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
  no knowledge of 3MF files, parsers, or archives.
- **`exporters/`** — turns model objects into external representations. `text_export.py` formats a
  `PrintJob` as TXT/CSV. `quote_export.py` (Milestone 2) formats a `PrintJob` + `QuoteBreakdown`
  as a human-readable quote report. Neither exporter knows how the job was obtained. Phase 3's PDF
  export will be a new file in this package alongside both.
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

## Extension points for later phases

- **Phase 3 (PDF quotes, packing lists, print queue)** — add `exporters/pdf_export.py` alongside
  `text_export.py` and `quote_export.py`. The GUI becomes a `ui/qt/` subpackage that calls the
  same `InspectionService` and `QuoteService` the console already uses.
- **Phase 4 (Inventory)** — a new `services/inventory_service.py` and its own models, likely
  consuming `PrintJob.filament_totals_by_material()` to decrement stock after a print is queued.

## Deliberately not built yet

No parser registry/plugin framework, no abstract factory, no settings/config system, no logging
framework. With exactly one slicer parser and one console UI, those would be speculative complexity
with no current caller. `SlicerProjectParser` gives just enough abstraction to add a second parser
without a rewrite; nothing more is justified until there's a second one to add.
