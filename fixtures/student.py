"""Canned student data for all four fake-portal tests.

Values are chosen to match exactly what the fake LOV popups and wizard steps
serve, so best_subject_match / best_option_match / best_programme_match all
find a hit.
"""

from app.automation.base import FieldMapping, PortalCredentials
from app.automation.challenge import ChallengeRequest


# ---------------------------------------------------------------------------
# Fake email challenge source (returns preset values instantly, no IMAP)
# ---------------------------------------------------------------------------

class FakeEmailChallengeSource:
    """Satisfies the EmailChallengeSource protocol; returns preset values."""

    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    async def get_values(self, request: ChallengeRequest) -> dict[str, str]:
        return self._values


# ---------------------------------------------------------------------------
# Shared base mapping (fields common to all unis)
# ---------------------------------------------------------------------------

_BASE = {
    "surname": "Dlamini",
    "first_names": "Thabo Sipho",
    "initials": "TS",
    "title": "MR",
    "id_number": "0001015009087",
    "date_of_birth": "01-JAN-2000",       # UJ DD-MON-YYYY format
    "gender": "Male",
    "marital_status": "Single",
    "home_language": "English",
    "ethnic_group": "AFRICAN",
    "sa_citizen": "Yes",
    "citizenship_code": "South Africa",   # UJ LOV option
    "citizenship_type": "SA Citizen",     # UCT select option
    "source_of_funding": "NSFAS",
    "email": "thabo.test@uniflo-test.invalid",
    "verify_email": "thabo.test@uniflo-test.invalid",
    "phone": "0821234567",                # applicant mobile (Wits _step_contact)
    "sa_cell": "0821234567",
    "has_sa_cell": "Yes",
    "apply_residence": "No",
    "has_disability": False,
    # Address
    "street_address_1": "123 Test Street",
    "street_address_2": "Soweto",
    "street_address_3": "Johannesburg",
    "street_address_4": "Gauteng",
    "address_line_1": "123 Test Street",
    "address_line_2": "Soweto",
    "suburb": "Soweto",
    "city": "Johannesburg",
    "postal_code": "1804",
    "population_group": "Black",
    # NOK / account contact
    "nok_surname": "Dlamini",           # required by Wits _require_next_of_kin
    "nok_name": "Nomvula Dlamini",
    "nok_phone": "0831234567",          # must differ from applicant's phone
    "nok_mobile": "0831234567",
    "nok_email": "nomvula@uniflo-test.invalid",
    "account_name": "Nomvula Dlamini",
    "account_email": "nomvula@uniflo-test.invalid",
    "account_addr_1": "123 Test Street",
    "account_addr_2": "Soweto",
    "account_addr_3": "Johannesburg",
    "account_addr_4": "Gauteng",
    "account_postal_code": "1804",
    # Matric
    "matric_year": "2024",
    "final_school_year": "2024",
    "examination_month": "November",
    "exam_number": "G24NS123456",
    "examining_authority": "DBE (NSC)",
    "ug_or_pg": "Undergraduate",
    "upgrading": "No",
    "matric_type": "SA Matric",
    "endorsement": "CURRENTLY IN GR.12",
    "current_activity": "Completing Matric",
    "present_activity": "GRADE 12 PUPIL",
    "studied_before": "No",
    # Subjects — 7 subjects (Wits requires ≥5)
    "subjects": [
        {"name": "Mathematics", "percentage": 75},
        {"name": "English Home Language", "percentage": 70},
        {"name": "Life Orientation", "percentage": 80},
        {"name": "Physical Sciences", "percentage": 65},
        {"name": "Accounting", "percentage": 72},
        {"name": "Geography", "percentage": 68},
        {"name": "History", "percentage": 74},
    ],
    # Previous studies
    "school": "SOWETO SECONDARY SCHOOL",
    # Programme
    "academic_year": "2026",
    "application_year": "2026",
    "applying_for": "Curricular Courses",
    "faculty": "ENGINEERING&BUILT ENVIRONMENT",
    "programme": "Computer Science",
    "year_of_study": "FIRST YEAR",
    "choice_level": "Undergraduate",
    # UCT extras
    "race": "African",
    "sex": "Male",
    "sa_id": "0001015009087",
    "applied_before": "No",
    "nbt_registration_number": "9312345678",
    "nbt_year": "2025",
    "nbt_date": "2025-09-01",
}

UJ_MAPPING = FieldMapping(values={
    **_BASE,
    # UJ home_language select uses uppercase "ENGLISH" (real ITS portal option)
    "home_language": "ENGLISH",
})

_UCT_EXCLUDED = {"school"}  # omit → _step5_school skips the _find_school search modal
UCT_MAPPING = FieldMapping(values={
    k: v for k, v in {
        **_BASE,
        # NBT required by UCT _require_nbt
        "nbt_registration_number": "9312345678",
        "nbt_year": "2025",
    }.items()
    if k not in _UCT_EXCLUDED
})

_WITS_EXCLUDED = {"school"}  # omit → _step_secondary skips the _find_school modal
WITS_MAPPING = FieldMapping(values={
    k: v for k, v in {
        **_BASE,
        "programme": "Computer Science",
        # Wits _step_personal uses label-driven title/gender selects
        "title": "Mr",
        "gender": "Male",
        # Wits NOK (required)
        "nok_surname": "Dlamini",
        "nok_phone": "0831234567",
        "nok_email": "nomvula@uniflo-test.invalid",
        # Wits _step_demographics
        "marital_status": "Single",
        "home_language": "English",
        "population_group": "Black",
    }.items()
    if k not in _WITS_EXCLUDED
})

# suburb/city/postal_code are kept — _section_contact resolves them via the
# postcode modal. school is omitted so _section_secondary skips _find_school.
_UP_EXCLUDED = {"school"}
UP_MAPPING = FieldMapping(values={
    k: v for k, v in {
        **_BASE,
        "programme": "Computer Science",
        "gender": "Male",
        "home_language": "English",
    }.items()
    if k not in _UP_EXCLUDED
})


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

UJ_CREDS = PortalCredentials(username="", password="")

UCT_CREDS = PortalCredentials(
    username="test@uniflo-test.invalid",
    password="Test123!",
    extra={
        "first_name": "Thabo",
        "last_name": "Dlamini",
        "date_of_birth": "2000-01-01",
        "id_number": "0001015009087",
        "email": "thabo.test@uniflo-test.invalid",
        "application_year": "2026",
    },
)

WITS_CREDS = PortalCredentials(
    username="WTS123456",
    password="Test123!",
    extra={
        "nationality": "South Africa",
        # adapter reads extra["id_number"] (the form field is named national_id)
        "id_number": "0001015009087",
        "title": "Mr",
        "first_name": "Thabo",
        "middle_names": "Sipho",
        "last_name": "Dlamini",
        # Wits split_dob expects dd/mm/yyyy
        "date_of_birth": "01/01/2000",
        "gender": "Male",
        "email": "thabo.test@uniflo-test.invalid",
        "mobile": "0821234567",
        "agreement_consented": "true",
    },
)

WITS_FAKE_CHALLENGE = FakeEmailChallengeSource({
    "temporary_id": "WTS123456",   # key must match expected_fields
    "password": "TempPass1!",
})

UP_CREDS = PortalCredentials(
    username="APP123456",
    password="Test123!",
    extra={
        "first_name": "Thabo",
        "last_name": "Dlamini",
        # UP _iso_date accepts dd/mm/yyyy
        "date_of_birth": "01/01/2000",
        "id_number": "0001015009087",
        "email": "thabo.test@uniflo-test.invalid",
        "application_year": "2026",
    },
)

UP_FAKE_CHALLENGE = FakeEmailChallengeSource({
    "application_id": "APP123456",
    "password": "Test123!",
})


# ---------------------------------------------------------------------------
# Phase 6 variants: international (passport) + upgrading applicants
# ---------------------------------------------------------------------------

# UJ international: oapCitizenType=No reveals passport + study-permit + gender.
UJ_INTL_MAPPING = FieldMapping(values={
    **UJ_MAPPING.values,
    "sa_citizen": "No",
    "citizenship_code": "Zimbabwe",       # non-SA country (UJ LOV option)
    "passport_number": "ZW1234567",
    "study_permit": "Study Visa",         # #oapStudyPermit option
    "gender": "F Female",                 # explicit on the international branch
})

# UCT international: Step-2 citizenship swaps the SA-ID block for the Passport
# Information add-row table. sa_id omitted so _step2_personal takes the passport
# branch; passport_citizenship_status fuzzy-falls-back to modal "Citizen".
UCT_INTL_MAPPING = FieldMapping(values={
    **{k: v for k, v in UCT_MAPPING.values.items() if k != "sa_id"},
    "citizenship_type": "International (Non-SA Citizen)",
    "passport_country": "Zimbabwe",
    "passport_citizenship_status": "International",
    "passport_number": "ZW1234567",
})

# Wits international: a non-SA nationality flips the National ID Type to passport
# in the Create Application ID form (login), which then receives the passport.
WITS_INTL_CREDS = PortalCredentials(
    username="WTS123456",
    password="Test123!",
    extra={
        k: v for k, v in {**WITS_CREDS.extra} .items() if k != "id_number"
    } | {
        "nationality": "Zimbabwe",
        "passport_number": "ZW1234567",
    },
)

# UP upgrading: repeats a prior matric — the data-driven Secondary/Demographic
# sections select the repeating tell_us_more + Bachelor's exemption + Grade 12.
UP_UPGRADING_MAPPING = FieldMapping(values={
    **UP_MAPPING.values,
    "tell_us_more": "I am repeating school /subjects",
    "highest_grade": "Grade 12",
    "exemption_type": "Admit to Bachelor Studies",
})
