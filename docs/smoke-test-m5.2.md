# Smoke Test — Milestone 5.2 Quote History Browser

**Commit:** _(fill in after push)_
**Date:** 2026-07-12
**Tester:** _(your name)_

---

## Prerequisites

- Virtual environment active
- Package installed (`pip install -e .`)
- `DriftPostBase.gcode.3mf` (or any `.3mf`) present in `Sample Projects\`
- 152/152 tests passing before starting

---

## Step 1 — Launch the app

```
geekcurio-app
```

**Expected:** Window opens titled `GeekCurio Print Manager` with two tabs: **New Quote** and
**Quote History**. No errors on launch.

---

## Step 2 — Generate a new quote (New Quote tab)

On the **New Quote** tab:

| Field | Value |
|---|---|
| Project File | `Sample Projects\DriftPostBase.gcode.3mf` (Browse…) |
| Profile | `Premium FDM / Custom Work` |
| Customer | `Asim` |
| Project Name | `4th Planet Battle Doggo` |

Click **Generate Quote**.

**Expected:** Quote Ref (e.g. `GCQ-2026-000012`), Total `£10.89`, status `Quote saved
successfully.` in green.

---

## Step 3 — Switch to Quote History

Click the **Quote History** tab.

**Expected:**
- The table refreshes automatically.
- The newly generated quote appears as the first row.
- Columns show: Ref, Issued date (e.g. `12 Jul 2026`), Customer (`Asim`), Project
  (`4th Planet Battle Doggo`), Total (`£10.89`).
- Detail area below the table still shows `—` placeholders.
- **Generate PDF** button is disabled.

---

## Step 4 — Select the quote

Click the new quote's row in the table.

**Expected:**
- Row highlights.
- Detail area populates:

| Field | Expected value |
|---|---|
| Quote Ref | `GCQ-2026-000012` (or whichever was generated) |
| Customer | `Asim` |
| Project | `4th Planet Battle Doggo` |
| Total | `£10.89` |
| Print Time | `1h 41m` |
| Filament | `66.6 g` |
| Plates | `1` |

- **Generate PDF** button becomes enabled.
- Status area is blank (no success/error yet).

---

## Step 5 — Cancel the PDF save dialog

Click **Generate PDF**.

**Expected:** A save-file dialog opens, pre-populated with `GCQ-2026-000012.pdf` in the current
directory.

Click **Cancel** (do not save).

**Expected:** Dialog closes. Status area remains blank — no false success message, no error.

---

## Step 6 — Generate PDF from history

Click **Generate PDF** again and this time accept the default path (or choose a location).

**Expected:** Status shows `PDF saved: GCQ-2026-000012.pdf` in green. The PDF file exists at the
chosen path and opens correctly.

---

## Step 7 — Empty state (optional, if starting fresh)

If the database is empty (first run), switch to **Quote History** before generating any quote.

**Expected:** Table is hidden. A calm message `No saved quotes yet.` is displayed. No crash or
error.

---

## Step 8 — Project display uses explicit name, not filename cleaning

In the history table and detail area, a quote saved with an explicit **Project Name** should
display that name as-is (e.g. `4th Planet Battle Doggo`), not the cleaned source filename.

A quote saved without a project name should show the cleaned source filename
(e.g. `DriftPostBase` — not `DriftPostBase.gcode`).

---

## Step 9 — Run the test suite

```
pytest --tb=short -q
```

**Expected:** `152 passed`

---

## Pass / Fail

| Step | Result | Notes |
|---|---|---|
| 1 — App launches with two tabs | | |
| 2 — New quote generated | | |
| 3 — History tab refreshes, quote appears | | |
| 4 — Selecting row populates details | | |
| 5 — Cancelling PDF dialog shows no false status | | |
| 6 — Generate PDF from history works | | |
| 7 — Empty state shown calmly (if applicable) | | |
| 8 — Project name display correct | | |
| 9 — 152 tests passing | | |

**Overall:** PASS / FAIL

**Tester sign-off:** ___________________________  **Date:** _______________
