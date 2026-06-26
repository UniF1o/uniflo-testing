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

# Show output for xfail tests
"C:\Users\andzi\Desktop\UniFlo\uniflo-api\.venv\Scripts\python.exe" -m pytest tests/test_wits.py -v -s
```

## Expected results

| Test | Expected |
|------|---------|
| `test_uj_fills_form` | PASS — UJ fake is fully implemented |
| `test_uct_fills_form` | PASS — UCT fake covers all 14 wizard steps |
| `test_wits_fills_form` | XFAIL (acceptable) — complex login + address modal |
| `test_up_fills_form` | XFAIL (acceptable) — postcode modal + complex login |

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
    ├── test_wits.py        # xfail(strict=False)
    └── test_up.py          # xfail(strict=False)
```

## Improving Wits / UP (promoting xfail → pass)

Both Wits and UP fakes are architecturally correct but a few interactions may
need tuning based on actual adapter behaviour:

- **Wits**: The address search modal in step 7 needs to close correctly after
  `VC_OA_WRK_SELECT$0` is clicked. Run with `-s` to see where it stops.

- **UP**: `_section_contact` calls `_set_city` which opens a postcode modal.
  The fake serves `/modal/postcode` with a `SELECT_BTN$0` row. If it fails,
  check that `UP_MAPPING` does NOT include `postal_code`/`suburb`/`city` (so
  `_set_city` raises `ValidationFailedError` early) — or complete the modal.
