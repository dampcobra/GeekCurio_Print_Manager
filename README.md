# GeekCurio Print Manager

A desktop application that automates the administrative side of GeekCurio's 3D printing
workflow — quoting, packing lists, print queue, and inventory — while leaving engineering and
slicing decisions to the operator.

This repository currently implements **Milestone 1**: the 3MF Project Inspector. It accepts a
`.3mf` file exported (sliced) from Bambu Studio or OrcaSlicer, extracts total print time and total
material usage, and displays them. See `docs/architecture.md` for how the codebase is organised and
how later phases (quoting, PDF export, inventory) are expected to build on this foundation.

## Setup

Requires Python 3.13+.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

## Running

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

Drop real exported `.3mf` files into `Sample Projects/` for manual testing — that folder is
gitignored aside from a placeholder, so it's a safe scratch space for your own project files.

## Testing

```
pytest
```

Tests build synthetic `.3mf` archives in memory, so they don't require a real sample file.

## Project Structure

See `docs/architecture.md` for the full breakdown of packages and responsibilities.
