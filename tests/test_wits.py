"""Test Wits adapter against the fake PeopleSoft Fluid portal.

Marked xfail(strict=False): the login + wizard flow is complex and some
steps may not yet be fully faked. Remove the xfail once the test passes
consistently.
"""

import uuid
import unittest.mock as mock

import pytest

from app.automation.adapters import wits as wits_mod
from app.automation.base import DocumentRef
from app.automation.runtime import run_job
from app.automation.results import RunOutcome
from conftest import start_server
from fake_portals.wits import make_wits_app
from fixtures.student import WITS_CREDS, WITS_FAKE_CHALLENGE, WITS_MAPPING


@pytest.fixture
async def wits_url():
    app = make_wits_app()
    url, runner = await start_server(app)
    yield url
    await runner.cleanup()


@pytest.fixture
def wits_docs(tmp_path: pytest.TempPathFactory) -> list[DocumentRef]:
    id_f = tmp_path / "id_copy.pdf"
    id_f.write_bytes(b"%PDF-1.4 fake")
    gr11_f = tmp_path / "grade11.pdf"
    gr11_f.write_bytes(b"%PDF-1.4 fake")
    return [
        DocumentRef(doc_type="ID_COPY", local_path=str(id_f), filename="id_copy.pdf"),
        DocumentRef(doc_type="GRADE11_RESULTS", local_path=str(gr11_f), filename="grade11.pdf"),
    ]


@pytest.mark.xfail(strict=False, reason="Wits login/wizard may not be fully faked yet")
async def test_wits_fills_form(wits_url: str, wits_docs: list[DocumentRef]) -> None:
    """Wits adapter runs login → fill_form → upload_documents against the fake
    portal and reports RunOutcome.FILLED (allow_submit=False)."""
    app_uuid = uuid.uuid4()
    with mock.patch.object(wits_mod, "LOGIN_URL", wits_url + "/"):
        from app.automation.adapters.wits import WitsAdapter
        adapter = WitsAdapter()
        adapter.set_challenge_source(
            WITS_FAKE_CHALLENGE,
            application_id=app_uuid,
            applicant_email=WITS_CREDS.extra["email"],
        )
        result = await run_job(
            adapter,
            credentials=WITS_CREDS,
            mapping=WITS_MAPPING,
            documents=wits_docs,
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None
