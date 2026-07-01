"""Test UCT adapter against the fake PeopleSoft Fluid portal."""

import unittest.mock as mock

import pytest

from app.automation.adapters import uct as uct_mod
from app.automation.base import DocumentRef
from app.automation.runtime import run_job
from app.automation.results import RunOutcome
from conftest import start_server
from fake_portals.uct import make_uct_app
from fixtures.student import UCT_CREDS, UCT_INTL_MAPPING, UCT_MAPPING


@pytest.fixture
async def uct_url():
    app = make_uct_app()
    url, runner = await start_server(app)
    yield url
    await runner.cleanup()


@pytest.fixture
def dummy_id_doc(tmp_path: pytest.TempPathFactory) -> DocumentRef:
    p = tmp_path / "id_copy.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    return DocumentRef(doc_type="ID_COPY", local_path=str(p), filename="id_copy.pdf")


async def test_uct_fills_form(uct_url: str, dummy_id_doc: DocumentRef) -> None:
    """UCT adapter runs login → fill_form → upload_documents against the fake
    portal and reports RunOutcome.FILLED (allow_submit=False)."""
    with (
        mock.patch.object(uct_mod, "LOGIN_URL", uct_url + "/login"),
        mock.patch.object(uct_mod, "CREATE_ACCOUNT_URL", uct_url + "/login"),
    ):
        from app.automation.adapters.uct import UCTAdapter
        adapter = UCTAdapter()
        result = await run_job(
            adapter,
            credentials=UCT_CREDS,
            mapping=UCT_MAPPING,
            documents=[dummy_id_doc],
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None


async def test_uct_international_fills_form(
    uct_url: str, dummy_id_doc: DocumentRef
) -> None:
    """International applicant: Step-2 citizenship 'International (Non-SA
    Citizen)' hides the SA-ID field and reveals the Passport Information add-row
    table; the adapter fills the passport modal (Country / Citizenship Status /
    Passport Number) and completes the wizard."""
    with (
        mock.patch.object(uct_mod, "LOGIN_URL", uct_url + "/login"),
        mock.patch.object(uct_mod, "CREATE_ACCOUNT_URL", uct_url + "/login"),
    ):
        from app.automation.adapters.uct import UCTAdapter
        adapter = UCTAdapter()
        result = await run_job(
            adapter,
            credentials=UCT_CREDS,
            mapping=UCT_INTL_MAPPING,
            documents=[dummy_id_doc],
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None
