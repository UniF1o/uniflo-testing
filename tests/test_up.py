"""Test UP adapter against the fake PeopleSoft Fluid portal.

Covers the full walk: the new-application form (captcha decoded from image
filenames) + email challenge + sign-in, then the single-page wizard's
sections — Contact Details (postcode modal), Secondary subjects grid, Study
Choice (programme search modal) — and the document upload modal.
"""

import uuid
import unittest.mock as mock

import pytest

from app.automation.adapters import up as up_mod
from app.automation.base import DocumentRef
from app.automation.runtime import run_job
from app.automation.results import RunOutcome
from conftest import start_server
from fake_portals.up import make_up_app
from fixtures.student import (
    UP_CREDS,
    UP_FAKE_CHALLENGE,
    UP_MAPPING,
    UP_UPGRADING_MAPPING,
)


@pytest.fixture
async def up_url():
    app = make_up_app()
    url, runner = await start_server(app)
    yield url
    await runner.cleanup()


@pytest.fixture
def up_docs(tmp_path: pytest.TempPathFactory) -> list[DocumentRef]:
    id_f = tmp_path / "id_copy.pdf"
    id_f.write_bytes(b"%PDF-1.4 fake")
    gr11_f = tmp_path / "grade11.pdf"
    gr11_f.write_bytes(b"%PDF-1.4 fake")
    return [
        DocumentRef(doc_type="ID_COPY", local_path=str(id_f), filename="id_copy.pdf"),
        DocumentRef(doc_type="GRADE11_RESULTS", local_path=str(gr11_f), filename="grade11.pdf"),
    ]


async def test_up_fills_form(up_url: str, up_docs: list[DocumentRef]) -> None:
    """UP adapter runs login → fill_form → upload_documents against the fake
    portal and reports RunOutcome.FILLED (allow_submit=False)."""
    app_uuid = uuid.uuid4()
    with mock.patch.object(up_mod, "PORTAL_URL", up_url + "/"):
        from app.automation.adapters.up import UPAdapter
        adapter = UPAdapter()
        adapter.set_challenge_source(
            UP_FAKE_CHALLENGE,
            application_id=app_uuid,
            applicant_email=UP_CREDS.extra["email"],
        )
        result = await run_job(
            adapter,
            credentials=UP_CREDS,
            mapping=UP_MAPPING,
            documents=up_docs,
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None


async def test_up_upgrading_fills_form(
    up_url: str, up_docs: list[DocumentRef]
) -> None:
    """Upgrading applicant: the data-driven Secondary/Demographic sections
    select the repeating 'Tell us more', Grade 12 highest grade, and the
    Bachelor's exemption — no adapter code change, just the new option values."""
    app_uuid = uuid.uuid4()
    with mock.patch.object(up_mod, "PORTAL_URL", up_url + "/"):
        from app.automation.adapters.up import UPAdapter
        adapter = UPAdapter()
        adapter.set_challenge_source(
            UP_FAKE_CHALLENGE,
            application_id=app_uuid,
            applicant_email=UP_CREDS.extra["email"],
        )
        result = await run_job(
            adapter,
            credentials=UP_CREDS,
            mapping=UP_UPGRADING_MAPPING,
            documents=up_docs,
            allow_submit=False,
            headless=True,
        )

    assert result.outcome == RunOutcome.FILLED, (
        f"Expected FILLED, got {result.outcome}; failure={result.failure}"
    )
    assert result.failure is None
