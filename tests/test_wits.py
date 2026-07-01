"""Test Wits adapter against the fake PeopleSoft Fluid portal.

Covers the full walk: the two-phase Create Application ID login (captcha
decoded from image filenames + email challenge + forced password set), the
17-step wizard (info-only steps 1/14/15, the Gr11 subject grid, address-search
modal), and the document upload modal.
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
from fixtures.student import (
    WITS_CREDS,
    WITS_FAKE_CHALLENGE,
    WITS_INTL_CREDS,
    WITS_MAPPING,
)


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


async def test_wits_international_fills_form(
    wits_url: str, wits_docs: list[DocumentRef]
) -> None:
    """International applicant: a non-SA nationality in Create Application ID
    flips the National ID Type to passport, which receives the passport number
    (credentials carry no SA id_number). The wizard then completes as usual."""
    app_uuid = uuid.uuid4()
    with mock.patch.object(wits_mod, "LOGIN_URL", wits_url + "/"):
        from app.automation.adapters.wits import WitsAdapter
        adapter = WitsAdapter()
        adapter.set_challenge_source(
            WITS_FAKE_CHALLENGE,
            application_id=app_uuid,
            applicant_email=WITS_INTL_CREDS.extra["email"],
        )
        result = await run_job(
            adapter,
            credentials=WITS_INTL_CREDS,
            mapping=WITS_MAPPING,
            documents=wits_docs,
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None
