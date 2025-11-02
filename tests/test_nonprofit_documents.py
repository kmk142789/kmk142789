from datetime import date

from echo.workflows.nonprofit_documents import (
    BoardMember,
    ContactProfile,
    FilingProfile,
    NonprofitPaperworkGenerator,
)


def make_generator() -> NonprofitPaperworkGenerator:
    profile = FilingProfile(
        legal_name="Little Footsteps Learning Cooperative",
        doing_business_as="Little Footsteps",
        address_line1="456 Hope Ave",
        address_line2="Suite 12",
        city="Austin",
        state="TX",
        postal_code="73301",
        mission_statement="To provide equitable, bilingual childcare centred on family partnership.",
        website="https://littlefootsteps.example.org",
        programs=["Infant care cohorts", "Family support navigation"],
        incorporation_state="Texas",
    )
    contact = ContactProfile(
        name="Echo Rivera",
        title="Executive Director",
        email="echo@littlefootsteps.example.org",
        phone="512-555-0102",
    )
    board = [
        BoardMember(name="Maya Chen", title="Board Chair", term_length_years=3),
        BoardMember(name="Amina Ortiz", title="Treasurer", term_length_years=2),
    ]
    generator = NonprofitPaperworkGenerator(
        profile,
        contact,
        board,
        childcare_capacity=36,
        licensing_requirements=[
            "Fire marshal inspection report",
            "Water quality lab results",
            "Comprehensive background checks for staff",
        ],
    )
    return generator


def test_ein_request_letter_includes_core_details():
    generator = make_generator()
    document = generator.generate_ein_request_letter(request_date=date(2024, 5, 1))

    assert document.title == "IRS EIN Request Letter"
    assert "May 01, 2024" in document.body
    assert "Little Footsteps Learning Cooperative" in document.body
    assert "Infant care cohorts" in document.body
    assert "Echo Rivera" in document.body
    assert "Austin, TX 73301" in document.body


def test_articles_of_incorporation_lists_board_members():
    generator = make_generator()
    document = generator.generate_articles_of_incorporation()

    assert document.title == "Articles of Incorporation"
    assert "LITTLE FOOTSTEPS LEARNING COOPERATIVE" in document.body
    assert "• Maya Chen, Board Chair" in document.body
    assert "term: 2 years" in document.body
    assert "Echo Rivera" in document.body


def test_form_1023_outline_uses_single_line_address():
    generator = make_generator()
    document = generator.generate_form_1023_planning_document()

    assert document.title == "Form 1023 Preparation Outline"
    assert "Mailing address: 456 Hope Ave, Suite 12, Austin, TX 73301" in document.body
    assert "Public Charity Status" in document.body
    assert "Family support navigation" in document.body


def test_childcare_license_packet_expands_requirements():
    generator = make_generator()
    document = generator.generate_childcare_license_packet()

    assert document.title == "Childcare Licensing Checklist"
    assert "Facility Category" in document.body
    assert "Fire marshal inspection report" in document.body
    assert "Water quality lab results" in document.body
    assert "Echo will issue verifiable caregiver" in document.body
    assert "456 Hope Ave" in document.body
    assert "Austin, TX 73301" in document.body


def test_generate_all_returns_expected_documents():
    generator = make_generator()
    documents = generator.generate_all()

    assert set(documents.keys()) == {
        "ein_request_letter",
        "articles_of_incorporation",
        "form_1023_outline",
        "childcare_license_checklist",
        "submission_packet_overview",
    }
    assert all(doc.title and doc.body for doc in documents.values())


def test_submission_packet_overview_summarises_documents():
    generator = make_generator()
    overview = generator.generate_submission_packet_overview()

    assert overview.title == "Nonprofit Submission Packet"
    assert "NONPROFIT FORMATION SUBMISSION PACKET" in overview.body
    assert "IRS EIN Request Letter" in overview.body
    assert "Childcare Licensing Checklist" in overview.body
    assert "Track jurisdiction-specific licensing expirations" in overview.body
