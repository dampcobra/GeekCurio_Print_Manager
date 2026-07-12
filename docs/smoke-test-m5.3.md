# Smoke Test — Milestone 5.3 Open PDF Button

**Commit:** _(fill in after push)_
**Date:** 2026-07-12
**Tester:** _(your name)_

---

## Prerequisites

- Virtual environment active
- Package installed (`pip install -e .`)
- A `.3mf` file in `Sample Projects\`
- 152/152 tests passing before starting

---

## New Quote tab

### Step 1 — Generate a quote and export a PDF

1. Launch `geekcurio-app`.
2. On **New Quote**: browse for `.3mf`, select a profile, click **Generate Quote**.
3. Click **Generate PDF** and save to any location.

**Expected:**
- Status shows `PDF saved: GCQ-2026-NNNNNN.pdf` in green.
- **Open PDF** button becomes enabled.

---

### Step 2 — Open the PDF

Click **Open PDF**.

**Expected:** The system default PDF viewer opens the file. No error in the status area.

---

### Step 3 — Cancel a PDF save dialog; Open PDF state is unchanged

Click **Generate PDF** again, then click **Cancel** in the save dialog.

**Expected:** Dialog closes. Status message and **Open PDF** button state are unchanged from
Step 1 — the previously saved path is still remembered.

---

### Step 4 — Input change clears Open PDF

Change any input (e.g. switch the Profile dropdown).

**Expected:** **Open PDF** button becomes disabled. Status clears. The old PDF path is forgotten.

---

### Step 5 — Missing PDF graceful error

Generate a quote, generate a PDF, then delete or move the saved PDF file in Explorer.
Click **Open PDF**.

**Expected:** Status shows `PDF file not found. It may have been moved or deleted.` in red.
No crash.

---

## Quote History tab

### Step 6 — Generate PDF and open from history

1. Switch to **Quote History**.
2. Select any quote row.
3. Click **Generate PDF** and save.
4. Click **Open PDF**.

**Expected:** PDF opens in the system viewer. Status shows filename in green.

---

### Step 7 — Selecting a different row clears Open PDF

After Step 6, click a different row in the history table.

**Expected:** **Open PDF** button becomes disabled. Status clears.

---

### Step 8 — Cancel PDF from history; Open PDF state unchanged

With a row selected, click **Generate PDF**, then cancel the dialog.

**Expected:** **Open PDF** button state and status are unchanged from before the cancel.

---

### Step 9 — Missing PDF graceful error from history

Generate a PDF from a history row, delete the file in Explorer, then click **Open PDF**.

**Expected:** Status shows `PDF file not found. It may have been moved or deleted.` in red.
No crash.

---

## Step 10 — Run the test suite

```
pytest --tb=short -q
```

**Expected:** `152 passed`

---

## Pass / Fail

| Step | Result | Notes |
|---|---|---|
| 1 — Generate quote + PDF; Open PDF enabled | | |
| 2 — Open PDF launches viewer | | |
| 3 — Cancel save dialog; state unchanged | | |
| 4 — Input change disables Open PDF | | |
| 5 — Missing PDF shows friendly error | | |
| 6 — Open PDF from Quote History | | |
| 7 — Row change disables Open PDF | | |
| 8 — Cancel save from history; state unchanged | | |
| 9 — Missing PDF error from history | | |
| 10 — 152 tests passing | | |

**Overall:** PASS / FAIL

**Tester sign-off:** ___________________________  **Date:** _______________
