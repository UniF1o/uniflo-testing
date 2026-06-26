# uniflo-testing

Fake university portals + pytest harness for testing the UniFlo Playwright adapters
**without hitting real university websites or paying for AI API calls**.

## How it works

1. **Fake portals** (in `fake_portals/`) are aiohttp servers that mimic each
   university's HTML structure — same element IDs, page flow, LOV popups, and
   PeopleSoft Fluid Save/Next patterns.

2. **Tests** (in `tests/`) start a fake portal on a random local port, monkey-patch
   the adapter's `ENTRY_URL`/`LOGIN_URL`/`PORTAL_URL` constant to point at it,
   then run the real adapter with `allow_submit=False`.

3. Pass condition: `result.outcome == RunOutcome.FILLED` — the adapter navigated
   through `login → fill_form → upload_documents` without error.

No real network calls, no real credentials, no Claude API cost.

## Requirements

- uniflo-api must be checked out at `../uniflo-api` (sibling directory).
- Run everything from the **uniflo-api venv** (it has Playwright + all backend deps).

## Setup (one-time)

```bash
# From the uniflo-testing directory:
cd C:\Users\andzi\Desktop\UniFlo\uniflo-testing

# Install test-only deps into the uniflo-api venv
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\pip.exe" install aiohttp pytest pytest-asyncio

# Install Chromium (if not already installed in the venv)
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\playwright.exe" install chromium
```

## Running tests

```bash
cd C:\Users\andzi\Desktop\UniFlo\uniflo-testing

# Run all tests (~2-4 minutes, headless Chromium)
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\python.exe" -m pytest tests/ -v

# Run one adapter
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\python.exe" -m pytest tests/test_uj.py -v
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\python.exe" -m pytest tests/test_uct.py -v

# Verbose live logs (see exactly which step an adapter stops on)
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\python.exe" -m pytest tests/test_wits.py -v -s --log-cli-level=INFO
```

## CI

`.github/workflows/fake-portal-tests.yml` runs the whole suite on every push/PR,
weekly on a schedule, and on manual dispatch. It checks out **both** repos as
siblings (uniflo-api beside uniflo-testing, the layout `conftest.py` expects),
installs uniflo-api's pinned deps + Playwright Chromium, and runs `pytest`.

- **Cross-repo checkout:** uniflo-api is a separate private repo, so the workflow
  needs a token with read access to it — set the `UNIFLO_API_TOKEN` repo secret
  to a PAT / fine-grained token scoped to `UniF1o/uniflo-api`. (Falls back to the
  default `github.token`, which only works if uniflo-api is public.)
- **Dummy settings:** importing the adapters pulls in `app.config.Settings`
  (required fields), so the workflow sets fake `DATABASE_URL`/`SUPABASE_*`/etc.
  env vars. They must stay fake — the tests never touch the real DB/Supabase.
- **Testing a new adapter:** run the workflow via *Actions → Run workflow* and
  set the `uniflo_api_ref` input to the uniflo-api branch that adds it.

## Expected results

All four pass (`4 passed` — ~5 min headless):

| Test | Covers |
|------|--------|
| `test_uj_fills_form` | ITS Integrator multi-page form + LOV popups + subject loop |
| `test_uct_fills_form` | PeopleSoft Fluid 13 steps, phone + Gr11/Gr12 subject modals, upload |
| `test_wits_fills_form` | Two-phase Create-ID login + 17-step wizard + address modal + upload |
| `test_up_fills_form` | New-application login + single-page wizard (postcode/choice modals) + upload |

## File structure

```
uniflo-testing/
├── pyproject.toml          # aiohttp, pytest, pytest-asyncio deps
├── conftest.py             # sys.path wiring to uniflo-api, start_server helper
├── CLAUDE.md               # this file
├── fixtures/
│   └── student.py          # canned FieldMapping + PortalCredentials for all 4 unis
├── fake_portals/
│   ├── _fluid.py           # shared PeopleSoft Save/Next page factory + upload modal
│   ├── uj.py               # full UJ fake (ITS Integrator multi-page + LOV popups)
│   ├── uct.py              # UCT fake (PeopleSoft Fluid, 16 wizard steps)
│   ├── wits.py             # Wits fake (PeopleSoft Fluid, 17 steps + captcha)
│   └── up.py               # UP fake (PeopleSoft Fluid single-page wizard)
└── tests/
    ├── test_uj.py
    ├── test_uct.py
    ├── test_wits.py
    └── test_up.py
```

## Fake-portal gotchas (lessons from making all four pass)

- **Modal close must be async.** A modal's confirm/select button that the
  adapter clicks via `fluid.js_click(frame, …)` must NOT remove its own iframe
  synchronously — the `evaluate` then fails with "Frame was detached". Defer the
  removal with `setTimeout(…, 50)` (mirrors the portal's AJAX close).
- **Label association.** Adapters match selects/inputs by
  `el.labels[0].textContent.trim() === label`. A wrapping `<label>` works for an
  **input** (no text content) but breaks a **select** (its option text pollutes
  `textContent`) — use `<label for="id">Text</label><select id="id">` for selects.
- **Info-only steps.** Steps the adapter advances with a direct `Next` (no Save
  first — Welcome/Indemnity/Payment) need `step_handler(..., info_only=True)` so
  the Next button is visible on load.
- **Single visible button per text.** `fluid.click_button(page, "Go")` hits the
  first *visible* match — toggle inactive sections to `display:none` so only one
  "Go"/"Next" is visible at a time.
- **Search modals** need a `submitAction_win0(form, id)` function (the adapter
  calls it to run the PeopleSoft search) and result rows keyed by `SELECT_BTN$n`.
