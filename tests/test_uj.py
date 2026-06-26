"""Test UJ adapter against the fake ITS Integrator portal."""

import unittest.mock as mock

import pytest

from app.automation.adapters import uj as uj_mod
from app.automation.runtime import run_job
from app.automation.results import RunOutcome
from conftest import start_server
from fake_portals.uj import make_uj_app
from fixtures.student import UJ_CREDS, UJ_MAPPING


@pytest.fixture
async def uj_url():
    app = make_uj_app()
    url, runner = await start_server(app)
    yield url
    await runner.cleanup()


async def test_uj_fills_form(uj_url: str) -> None:
    """UJ adapter runs login → fill_form → upload_documents against the fake
    portal and reports RunOutcome.FILLED (allow_submit=False)."""
    with mock.patch.object(uj_mod, "ENTRY_URL", uj_url + "/"):
        from app.automation.adapters.uj import UJAdapter
        adapter = UJAdapter()
        result = await run_job(
            adapter,
            credentials=UJ_CREDS,
            mapping=UJ_MAPPING,
            documents=[],
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None
