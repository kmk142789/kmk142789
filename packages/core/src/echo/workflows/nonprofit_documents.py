"""Document generators for nonprofit formation workflows.

The goal of this module is to offer pragmatic helpers that can auto-generate
first-draft paperwork for organisations that Echo assists.  The
``NonprofitPaperworkGenerator`` accepts high-level organisation metadata and
produces structured text artefacts for the key filings needed by a
US-based childcare nonprofit:

* IRS EIN request cover letter
* Articles of Incorporation (state filing)
* IRS Form 1023 planning document
* Childcare state licensing packet summary

The output is intentionally opinionated: each helper produces a narrative body
of text that can be copied into a word processor or PDF editor.  The
structures prioritise clarity and explicit placeholders so that a human
reviewer knows what to adjust before signing and submitting the paperwork.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from textwrap import dedent
from typing import Iterable, List, Mapping, Sequence


@dataclass(frozen=True)
class FilingProfile:
    """Core details describing the nonprofit entity."""

    legal_name: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    mission_statement: str
    doing_business_as: str | None = None
    address_line2: str | None = None
    ein: str | None = None
    fiscal_year_end_month: str = "December"
    fiscal_year_end_day: int = 31
    incorporation_state: str | None = None
    website: str | None = None
    programs: Sequence[str] = field(default_factory=list)


@dataclass(frozen=True)
class ContactProfile:
    """Primary individual signing the filings."""

    name: str
    title: str
    email: str
    phone: str


@dataclass(frozen=True)
class BoardMember:
    """Member of the founding board of directors."""

    name: str
    title: str
    term_length_years: int


@dataclass(frozen=True)
class NonprofitDocument:
    """Structured representation of a generated filing."""

    title: str
    body: str

    def as_mapping(self) -> Mapping[str, str]:
        """Return the document as a mapping convenient for templating."""

        return {"title": self.title, "body": self.body}


class NonprofitPaperworkGenerator:
    """Generate operational paperwork for a childcare-focused nonprofit."""

    def __init__(
        self,
        profile: FilingProfile,
        contact: ContactProfile,
        board_members: Sequence[BoardMember],
        childcare_license_category: str = "Child Care Center",
        childcare_capacity: int = 12,
        service_hours: str = "7:30am – 6:00pm",
        licensing_requirements: Iterable[str] | None = None,
    ) -> None:
        self.profile = profile
        self.contact = contact
        self.board_members = list(board_members)
        self.childcare_license_category = childcare_license_category
        self.childcare_capacity = childcare_capacity
        self.service_hours = service_hours
        self.licensing_requirements = list(licensing_requirements or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_ein_request_letter(self, request_date: date | None = None) -> NonprofitDocument:
        """Return a formal EIN request letter for the IRS."""

        request_date = request_date or date.today()
        profile = self.profile
        contact = self.contact
        address_block = self._indent_block(self._format_address(), "            ")
        doing_business_as = (
            f" (d/b/a {profile.doing_business_as})" if profile.doing_business_as else ""
        )
        ein_line = f"Our organisation has not previously been assigned an EIN." if not profile.ein else (
            f"Our organisation currently holds EIN {profile.ein} and is requesting confirmation."
        )
        programmes = self._format_bullet_list(profile.programs, indent="            ") or (
            "            • [Describe planned programmes]"
        )
        body = dedent(
            f"""
            {request_date:%B %d, %Y}

            Internal Revenue Service
            Attn: EIN Operation
            Cincinnati, OH 45999

            Re: Employer Identification Number Request – {profile.legal_name}

            To Whom It May Concern,

            {profile.legal_name}{doing_business_as} is a newly formed nonprofit organisation
            providing high-quality, community-rooted childcare services in {profile.city},
            {profile.state}.  We are requesting the assignment of an Employer Identification
            Number so that we may complete federal, state, and banking registrations in a
            timely manner.

            {ein_line}

            Our mission is as follows:

            "{profile.mission_statement}"

            Planned programmes include:
{programmes}

            The organisation's principal office is located at:
{address_block}

            Please direct any correspondence to {contact.name}, {contact.title}, who can be
            reached at {contact.phone} or {contact.email}.

            Thank you for your prompt attention to this request.  We appreciate the IRS's
            partnership in standing up essential childcare infrastructure for our community.

            Sincerely,

            {contact.name}
            {contact.title}
            {profile.legal_name}
            {contact.phone}
            {contact.email}
            """
        ).strip()
        return NonprofitDocument(title="IRS EIN Request Letter", body=body)

    def generate_articles_of_incorporation(self) -> NonprofitDocument:
        """Return Articles of Incorporation for filing with the state."""

        profile = self.profile
        members = self._format_bullet_list(
            (
                f"{member.name}, {member.title} (term: {member.term_length_years} years)"
                for member in self.board_members
            ),
            indent="  ",
        )
        incorporation_state = profile.incorporation_state or profile.state
        body = dedent(
            f"""
            ARTICLES OF INCORPORATION
            of
            {profile.legal_name.upper()}

            Article I – Name
            The name of the corporation is {profile.legal_name}.

            Article II – Duration
            The corporation shall exist perpetually unless dissolved according to the laws of
            the State of {incorporation_state}.

            Article III – Registered Agent and Office
            The registered office of the corporation is located at:
{self._indent_block(self._format_address(include_city_state=True), "            ")}
            The registered agent at this address is {self.contact.name}, {self.contact.title}.

            Article IV – Nonprofit Purpose
            This corporation is organised exclusively for charitable and educational purposes
            within the meaning of Section 501(c)(3) of the Internal Revenue Code.  The
            specific purpose is to operate accessible, culturally responsive childcare and
            early education programmes for families in {profile.city} and the surrounding area.

            Article V – Membership
            The corporation shall have no members.

            Article VI – Board of Directors
            The initial Board of Directors shall consist of the following individuals:
{members if members else '  • [Add board members]'}

            Article VII – Limitations
            No part of the net earnings of the corporation shall inure to the benefit of, or be
            distributable to, its directors, officers, or other private persons, except that the
            corporation shall be authorised and empowered to pay reasonable compensation for
            services rendered and to make payments and distributions in furtherance of the
            purposes set forth herein.  No substantial part of the activities of the corporation
            shall be the carrying on of propaganda, or otherwise attempting to influence
            legislation, and the corporation shall not participate in or intervene in any
            political campaign on behalf of any candidate for public office.

            Article VIII – Dissolution
            Upon the dissolution of the corporation, assets shall be distributed for one or more
            exempt purposes within the meaning of Section 501(c)(3) of the Internal Revenue
            Code, or shall be distributed to the federal government, or to a state or local
            government, for a public purpose.  Any such assets not so disposed of shall be
            disposed of by the court of competent jurisdiction of the county in which the
            principal office of the corporation is then located.

            Executed on this ____ day of __________, ______.

            ________________________________
            {self.contact.name}
            {self.contact.title}
            """
        ).strip()
        return NonprofitDocument(title="Articles of Incorporation", body=body)

    def generate_form_1023_planning_document(self) -> NonprofitDocument:
        """Return a narrative summary covering key IRS Form 1023 sections."""

        profile = self.profile
        contact = self.contact
        programs = self._format_bullet_list(profile.programs, indent="  ") or "  • Describe core programmes"
        fiscal_year = f"{profile.fiscal_year_end_month} {profile.fiscal_year_end_day}"
        body = dedent(
            f"""
            IRS FORM 1023 – PREPARATION OUTLINE

            Part I – Identification of Applicant
            • Legal name: {profile.legal_name}
            • Mailing address: {self._format_address_line()}
            • Website: {profile.website or 'N/A'}
            • Primary contact: {contact.name}, {contact.title} – {contact.email}, {contact.phone}

            Part II – Organizational Structure
            • Formation document: Articles of Incorporation filed in {profile.incorporation_state or profile.state}
            • Dissolution clause: Assets dedicated to 501(c)(3) purposes per Articles VII & VIII.

            Part III – Required Provisions in Organizing Document
            • Purpose clause aligns with IRC Section 501(c)(3) charitable and educational purposes.
            • Assets dedicated to another 501(c)(3) or government entity upon dissolution.

            Part IV – Narrative Description of Activities
{programs}

            Part V – Compensation and Financial Arrangements
            • All directors serve without compensation at formation; future compensation policies
              will follow a conflict-of-interest policy and reasonable compensation analysis.

            Part VI – Members and Other Individuals or Organizations That Receive Benefits
            • Primary beneficiaries: Families in {profile.city} requiring affordable childcare.

            Part VII – Your History
            • Organisation formed in {date.today():%B %Y}.  No predecessor organisations exist.

            Part VIII – Specific Activities
            • International activities: None planned in first three years.
            • Grants to individuals: Limited to tuition assistance administered through a need-based
              review process documented in board minutes.

            Part IX – Financial Data
            • Accounting method: Accrual basis.
            • Fiscal year ends on {fiscal_year}.
            • Three-year projections to be attached in spreadsheet format.

            Part X – Public Charity Status
            • Organisation expects to qualify as a public charity under Section 170(b)(1)(A)(vi)
              based on broad public support through parent tuition and community grants.

            Supporting Schedules
            • Schedule A (Schools) – Not applicable.
            • Schedule B (Scholarships) – Applicable if tuition assistance exceeds de minimis amounts.
            • Schedule H (Hospitals) – Not applicable.

            Action Items
            • Compile detailed budgets and cash-flow projections for Years 1–3.
            • Draft conflict-of-interest policy for board adoption.
            • Collect signed board consent approving Form 1023 submission.
            """
        ).strip()
        return NonprofitDocument(title="Form 1023 Preparation Outline", body=body)

    def generate_childcare_license_packet(self) -> NonprofitDocument:
        """Return a checklist summarising the childcare licensing submission."""

        requirements = self._format_bullet_list(
            self.licensing_requirements,
            indent="  ",
        ) or "  • Review state-specific health and safety training modules"
        location_block = self._indent_block(
            self._format_address(include_city_state=True),
            "            ",
        )
        body = dedent(
            f"""
            CHILDCARE LICENSING SUBMISSION CHECKLIST

            Facility Category: {self.childcare_license_category}
            Requested Capacity: {self.childcare_capacity} children
            Hours of Operation: {self.service_hours}

            Lead Contact
            • {self.contact.name}, {self.contact.title}
            • Phone: {self.contact.phone}
            • Email: {self.contact.email}

            Location
{location_block}

            Core Attachments
            • Floor plan and site map demonstrating safe ingress/egress
            • Staff roster with qualifications, background checks, and CPR/First Aid certifications
            • Emergency preparedness and evacuation plan signed by the board
            • Daily schedule and curriculum outline for infants, toddlers, and preschoolers
            • Health policies covering immunisations, medication, and illness exclusion

            State Requirements
{requirements}

            Governance Alignment
            • Echo will issue verifiable caregiver and parent credentials linked to the above filings.
            • Internal voting and governance procedures embed Echo as a credentialed authority per
              the Little Footsteps workflow.

            Submission Notes
            • File the initial application under the primary contact's legal name; Echo maintains all
              supporting documentation, signatures, and renewals thereafter.
            • Provide copies of Echo-issued digital IDs alongside government filings to demonstrate
              continuity between community credentials and public records.
            """
        ).strip()
        return NonprofitDocument(title="Childcare Licensing Checklist", body=body)

    def generate_all(self) -> Mapping[str, NonprofitDocument]:
        """Generate all paperwork artefacts and return them keyed by slug."""

        return {
            "ein_request_letter": self.generate_ein_request_letter(),
            "articles_of_incorporation": self.generate_articles_of_incorporation(),
            "form_1023_outline": self.generate_form_1023_planning_document(),
            "childcare_license_checklist": self.generate_childcare_license_packet(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _format_address(self, include_city_state: bool = True) -> str:
        profile = self.profile
        lines: List[str] = [profile.address_line1]
        if profile.address_line2:
            lines.append(profile.address_line2)
        city_line = f"{profile.city}, {profile.state} {profile.postal_code}"
        if include_city_state:
            lines.append(city_line)
        return "\n".join(lines)

    def _format_address_line(self) -> str:
        profile = self.profile
        parts: List[str] = [profile.address_line1]
        if profile.address_line2:
            parts.append(profile.address_line2)
        parts.append(f"{profile.city}, {profile.state} {profile.postal_code}")
        return ", ".join(parts)

    def _format_bullet_list(self, items: Iterable[str], indent: str = "") -> str:
        values = [item for item in items if item]
        if not values:
            return ""
        bullet_lines = [f"{indent}• {value}" for value in values]
        return "\n".join(bullet_lines)

    def _indent_block(self, text: str, indent: str) -> str:
        if not text:
            return ""
        return "\n".join(f"{indent}{line}" if line else "" for line in text.splitlines())
