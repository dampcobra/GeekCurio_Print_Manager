# GeekCurio Print Manager

A desktop application that automates the administrative side of GeekCurio's 3D printing
workflow — quoting, packing lists, print queue, and inventory — while leaving engineering and
slicing decisions to the operator.

This repository implements **Milestone 1** (3MF Project Inspector) and **Milestone 2** (Quote
Generator). It accepts a `.3mf` file exported (sliced) from Bambu Studio or OrcaSlicer, extracts
print time and material usage, and calculates a suggested price using configurable pricing rules.
See `docs/architecture.md` for how the codebase is organised and how later phases (PDF export,
inventory) are expected to build on this foundation.

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

To use fully custom rates in a script, instantiate `PricingConfig` directly and pass it to `QuoteService`:

```python
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_service import QuoteService
from geekcurio_print_manager.exporters.quote_export import build_quote_report

config = PricingConfig(
    hourly_machine_rate=4.0,
    material_cost_per_gram=0.04,
    overhead_multiplier=1.15,
    markup_percentage=20.0,
)
job = InspectionService().inspect("my-project.3mf")
breakdown = QuoteService(config).calculate(job)
print(build_quote_report(job, breakdown))
```

Drop real exported `.3mf` files into `Sample Projects/` for manual testing — that folder is
gitignored aside from a placeholder, so it's a safe scratch space for your own project files.

## Testing

```
pytest
```

Tests build synthetic `.3mf` archives in memory, so they don't require a real sample file.

## Project Structure

See `docs/architecture.md` for the full breakdown of packages and responsibilities.
