# uniflo-testing

Fake university portals + a pytest harness for testing the UniFlo Playwright
adapters (UCT, UJ, Wits, UP) **without hitting real university websites or
paying for AI API calls**.

## How it works

1. **Fake portals** (`fake_portals/`) are aiohttp servers that mimic each
   university's HTML structure — the same element IDs, page flow, LOV popups,
   and PeopleSoft Fluid Save/Next patterns the real adapters expect.

2. **Tests** (`tests/`) start a fake portal on a random local port, monkey-patch
   the adapter's `ENTRY_URL` / `LOGIN_URL` / `PORTAL_URL` constant to point at
   it, then run the **real, unmodified adapter** from `uniflo-api` with
   `allow_submit=False`.

3. Pass condition: `result.outcome == RunOutcome.FILLED` — the adapter walked
   `login → fill_form → upload_documents` without error and stopped before
   submitting.

No real network calls, no real credentials, no Claude API cost.

## Requirements

- `uniflo-api` checked out at `../uniflo-api` (sibling directory).
- Run everything from the **uniflo-api venv** (it has Playwright + backend deps).

See [`CLAUDE.md`](CLAUDE.md) for setup and run commands.
