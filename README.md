# GeekCurio Print Manager

A desktop application that automates the administrative side of GeekCurio's 3D printing
workflow — quoting, packing lists, print queue, and inventory — while leaving engineering and
slicing decisions to the operator.

This repository implements four milestones:

- **Milestone 1 — 3MF Project Inspector**: parse a `.3mf` file exported from Bambu Studio or
  OrcaSlicer and extract print time, material usage, and per-plate detail.
- **Milestone 2 — Quote Generator**: calculate a price from configurable pricing rules using five
  built-in profiles. All monetary values use `decimal.Decimal` for exact currency arithmetic.
- **Milestone 3 — Quote Persistence**: every generated quote is automatically saved to a local
  SQLite database (`%LOCALAPPDATA%\GeekCurio\GCPM\gcpm.sqlite`) and assigned a permanent
  reference number in the format `GCQ-YYYY-NNNNNN` (e.g. `GCQ-2026-000001`). The sequence never
  resets. Profile values are snapshotted at save time so historical quotes are immutable.
- **Milestone 4 — PDF Quote Output**: export any saved quote to a customer-facing PDF using its
  reference number. PDFs are generated from the persisted record — pricing is never recalculated.
- **Milestone 4.2 — Customer and Project Display Names**: optional `--customer` and `--project`
  arguments allow clean, human-readable names on the PDF without altering the stored source
  filename.

See `docs/architecture.md` for how the codebase is organised and how later milestones (PDF export,
GUI) are expected to build on this foundation.

## Setup

Requires Python 3.13+.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

## Running

### 3MF Project Inspector

```
python -m geekcurio_print_manager "Sample Projects\your-file.3mf"
```

Or omit the path to be prompted for one interactively:

```
python -m geekcurio_print_manager
```

Or, after the editable install, use the console script:

```
geekcurio-print-manager "Sample Projects\your-file.3mf"
```

### Quote Generator

```
geekcurio-quote "Sample Projects\your-file.3mf"
geekcurio-quote "Sample Projects\your-file.3mf" resin
geekcurio-quote "Sample Projects\your-file.3mf" premium_fdm
```

Or omit the path to be prompted:

```
geekcurio-quote
```

List all available pricing profiles:

```
geekcurio-quote --list
```

Available profiles: `fdm_pla` (default), `fdm_petg`, `resin`, `premium_fdm`, `internal_test`.

**Optional: customer and project display names**

Use `--customer` and `--project` to attach human-readable names to a quote. These are saved with
the quote and used on the PDF — they do not affect pricing and do not change the stored source
filename.

```
geekcurio-quote "Sample Projects\DriftPostBase.gcode.3mf" --customer "Asim" --project "4th Planet Battle Doggo"
```

- `--customer NAME` — adds a `Customer:` line to the PDF (omitted if not provided).
- `--project NAME` — overrides the project display name on the PDF (falls back to the cleaned
  filename if not provided: `DriftPostBase.gcode.3mf` → `DriftPostBase`).
- Blank or whitespace-only values are treated as absent.

Every quote is automatically saved and assigned a reference number (`GCQ-YYYY-NNNNNN`), which
appears in the output:

```
GeekCurio Quote: DriftPostBase.gcode.3mf  [FDM — PLA (Standard)]
Ref: GCQ-2026-000001
...
```

To use fully custom rates in a script, instantiate `PricingConfig` directly and pass it to `QuoteService`:

```python
from decimal import Decimal
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_service import QuoteService
from geekcurio_print_manager.exporters.quote_export import build_quote_report

config = PricingConfig(
    hourly_machine_rate=Decimal("4.00"),
    material_cost_per_gram=Decimal("0.04"),
    overhead_multiplier=Decimal("1.15"),
    markup_percentage=Decimal("20"),
)
job = InspectionService().inspect("my-project.3mf")
breakdown = QuoteService(config).calculate(job)
print(build_quote_report(job, breakdown))
```

### PDF Quote Generator

Generate a customer-facing PDF from any saved quote reference:

```
geekcurio-quote-pdf GCQ-2026-000001
```

This creates `GCQ-2026-000001.pdf` in the current directory.

Specify an output path with `--output` (or `-o`):

```
geekcurio-quote-pdf GCQ-2026-000001 --output quotes\asim-project.pdf
```

If the output path points to an existing directory, the PDF is placed inside it using the
reference as the filename. Parent directories are created automatically if they do not exist.
The PDF always reflects the values that were saved — totals are never recalculated.

Drop real exported `.3mf` files into `Sample Projects/` for manual testing — that folder is
gitignored aside from a placeholder, so it's a safe scratch space for your own project files.

## Testing

```
pytest
```

Tests build synthetic `.3mf` archives in memory, so they don't require a real sample file.

## Project Structure

See `docs/architecture.md` for the full breakdown of packages and responsibilities.
