# Phase 6 — Applicant-type + citizenship coverage (offline harness)

> `uniflo-testing` half of a cross-repo plan. Backend (adapters/mapping/schema) lives in
> `uniflo-api/docs/phase-6/`; frontend in `uniflo-web/docs/phase-6/`.
> **Status: plan only. No implementation until research PRs #80 (UJ) and #82 (UP) are merged.**

## Context

The Phase 3 portal-research effort (UCT #78, Wits #79, UJ #80, UP #82) mapped how each portal's
form branches by applicant type and citizenship. The `uniflo-api` adapters are being extended to
cover those branches (see the backend plan): **upgrading/repeating** (newly unblocked) and
**international/non-SA citizen with passport + permit** (newly added), on top of today's
still-in-G12 / completed-matric / gap-year / employed for SA citizens.

This repo runs the **real, unmodified adapters** from `uniflo-api` against aiohttp **fake portals**
with `allow_submit=False`; the pass condition is `RunOutcome.FILLED`. Today the harness only proves
the **SA-citizen / current-Grade-12** path: there is a single `_BASE` fixture in
`fixtures/student.py` ("Thabo Dlamini", `sa_citizen="Yes"`, `upgrading="No"`,
`endorsement="CURRENTLY IN GR.12"`), and the four fakes render only that flow. **The adapters' new
branches will ship untested offline unless the fakes replicate their conditional reveals.**

### Scope notes from research (must respect)
- **UP international is signup-gated** — the UP adapter never reaches it. UP gets the **upgrading**
  branch only; no international fake/fixture/test for UP.
- **Stellenbosch** has no adapter — out of scope.
- **Grade 10 / Grade 11 / at-university are profile-only** (apply-blocked in the frontend/guard) —
  they never reach an adapter, so **no fake-portal flow, fixture, or harness test** is needed for
  them here. The adapter-reaching new branches are only: international (UJ/UCT/Wits) and upgrading
  (UJ/UCT/Wits/UP).
- **September prelims (`grade_12_september`)** are just additional interim subject marks the mapper
  merges — no new fake reveal. A completed/upgrading fixture **may** carry a prelim record to
  exercise the merge, but the fakes need no new page for it.

---

## Workstream F — Fakes, fixtures, harness

**F1. Fixtures** — `fixtures/student.py`
Add international and upgrader `FieldMapping` + `PortalCredentials` variants per portal (e.g.
`UJ_INTL_MAPPING` / `UJ_UPGRADE_MAPPING`, `UCT_INTL_MAPPING`, `WITS_INTL_MAPPING`,
`UP_UPGRADE_MAPPING`). Derive from `_BASE` and override the branch keys:
- **International:** `sa_citizen="No"`, `citizenship_type`/`citizenship_status` (e.g. UCT
  "International (Non-SA Citizen)"), `citizenship_code`/`nationality` to a real country,
  `passport_number`, `study_permit` (a value present in the UJ permit LOV), explicit
  `gender`/`date_of_birth`.
- **Upgrading:** `upgrading="Yes"`, `endorsement`/`present_activity` for a completed-matric
  upgrader, `current_activity="Upgrading matric"`, subjects from the Gr12-final set.
Values must match exactly what the fake LOV popups serve so the fuzzy matchers
(`best_subject_match` / `best_option_match` / `best_programme_match`) find a hit.

**F2. Fake portals** — `fake_portals/{uj,uct,wits,up}.py` (+ shared `_fluid.py`)
Render the new conditional reveals so the adapter's new code paths execute:
- **uj.py** (ITS Integrator): `oapCitizenType` select; `="No"` reveals `oapPPnumber` (passport),
  `oapStudyPermit` LOV (the 17-option permit set), explicit gender/DOB, and hides SA-ID. Add the
  `oapStudUpgrade` field for the upgrading branch.
- **uct.py** (PeopleSoft Fluid): Step-2 "Type of Citizenship or Residency" select that swaps the
  SA-ID block ↔ the Passport Information add-row table (Country / Citizenship Status / Passport
  Number). Mirror the AJAX hazard where toggling citizenship blanks the SA-ID field.
- **wits.py**: nationality select that auto-sets National ID Type → reveals the passport field.
  The upgrading path already routes through the Step-3 Main-Activity value already modelled.
- **up.py**: add the upgrading `exemption_type` / "Tell us more" option (no international branch).

Respect the documented fake-portal gotchas (CLAUDE.md): async modal close (`setTimeout 50`),
`<label for="id">` on selects, single visible button per text, search-modal `submitAction_win0`.

**F3. Harness tests** — `tests/test_{uj,uct,wits,up}.py`
Add per-branch cases that start the fake, monkey-patch the adapter's `ENTRY_URL`/`LOGIN_URL`/
`PORTAL_URL`, run the real adapter with `allow_submit=False`, and assert `RunOutcome.FILLED`:
`test_uj_fills_international`, `test_uj_fills_upgrading`, `test_uct_fills_international`,
`test_wits_fills_international`, `test_up_fills_upgrading`. Follow the existing
`test_uj_fills_form` pattern.

**F4. CI** — `.github/workflows/fake-portal-tests.yml`
The workflow checks out `uniflo-api` as a sibling. When running this branch's suite, set the
`uniflo_api_ref` input to `feature/applicant-type-citizenship` so the fakes run against the new
adapter code (Actions → Run workflow). Keep this repo's PR in lock step with the `uniflo-api`
adapter PR — neither merges green without the other.

> Note: leave the pre-existing uncommitted `tests/test_uj.py` working-tree change alone (not part
> of this plan).

---

## Verification

From `uniflo-testing`, using the `uniflo-api` venv (per CLAUDE.md):
```
"…/uniflo-api/.venv/Scripts/python.exe" -m pytest tests/ -v
```
All existing + new branch tests report `FILLED`. Run against the `feature/applicant-type-citizenship`
checkout of `uniflo-api` (sibling dir) so the new adapter code is under test.

---

## Execution gating (user directive)
1. **Now:** this plan PR only.
2. **Hold:** do not start Workstream F until research PRs **#80 (UJ)** and **#82 (UP)** are merged,
   and in lock step with the `uniflo-api` adapter work (Workstream C).
3. **Then:** F1 → F2 → F3, tracking the adapter branch via `uniflo_api_ref`.
