# Smoke Test — Milestone 5.0 Desktop GUI

**Commit:** `9094963`
**Date:** 2026-07-12
**Tester:** _(your name)_

---

## Prerequisites

- Virtual environment active
- Package installed (`pip install -e .`)
- `DriftPostBase.gcode.3mf` present in `Sample Projects\`
- 144/144 tests passing before starting

---

## Step 1 — Launch the app

```
geekcurio-app
```

**Expected:** A window titled `GeekCurio Print Manager` opens. No errors or crashes on startup.

---

## Step 2 — Select a project file

Click **Browse…** and navigate to:

```
Sample Projects\DriftPostBase.gcode.3mf
```

**Expected:** The file path appears in the Project File field. The status area remains blank.

---

## Step 3 — Select a profile

Open the Profile dropdown and select:

```
Premium FDM / Custom Work
```

---

## Step 4 — Enter customer and project name

| Field | Value |
|---|---|
| Customer | `Asim` |
| Project Name | `4th Planet Battle Doggo` |

---

## Step 5 — Generate the quote

Click **Generate Quote**.

**Expected result area:**

| Field | Expected value |
|---|---|
| Quote Ref | `GCQ-2026-NNNNNN` (next in sequence) |
| Total | `£10.89` |
| Print Time | `1h 41m` |
| Filament | `66.6 g` |
| Plates | `1` |
| Status line | `Quote saved successfully.` (green text) |

> **Baseline source:** CLI run of the same file with `premium_fdm` on 2026-07-12 produced
> `GCQ-2026-000004` with Total `£10.89`, 66.6 g, 1.68 hrs. The GUI must produce identical numbers.

---

## Step 6 — Verify blank field normalisation

Clear both Customer and Project Name fields (leave them empty). Click **Generate Quote** again.

**Expected:** Quote saves successfully. No error about empty strings.

---

## Step 7 — Verify error handling

Clear the Project File field is not possible directly (it is read-only), but click **Generate Quote**
with no file selected (restart the app fresh, do not browse for a file).

**Expected:** Red status text: `Please select a .3mf project file first.` No crash.

---

## Step 8 — Run the test suite

```
pytest --tb=short -q
```

**Expected:** `144 passed`

---

## Pass / Fail

| Step | Result | Notes |
|---|---|---|
| 1 — App launches | | |
| 2 — File picker | | |
| 3 — Profile dropdown | | |
| 4 — Customer / project fields | | |
| 5 — Quote generated, numbers correct | | |
| 6 — Blank fields normalised | | |
| 7 — Error handling | | |
| 8 — 144 tests passing | | |

**Overall:** PASS / FAIL

**Tester sign-off:** ___________________________  **Date:** _______________
