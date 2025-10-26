"""Digital identity playbooks for Lil Footsteps parents and providers."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class WalletOption:
    """Wallet pathway with onboarding and recovery guidance."""

    name: str
    category: str
    provider: str
    onboarding_steps: Sequence[str]
    recovery_model: str
    support_channels: Sequence[str]


@dataclass(frozen=True)
class CredentialChannel:
    """Verifiable credential distribution channel."""

    label: str
    medium: str
    description: str
    security_features: Sequence[str]
    data_retention: str


@dataclass(frozen=True)
class QrAccessPolicy:
    """QR code verification guardrails for childcare providers."""

    scanner_role: str
    verification_steps: Sequence[str]
    offline_fallback: str
    audit_log: str


@dataclass(slots=True)
class DigitalIdentityToolkit:
    """Compose wallet, credential, and access policies for Lil Footsteps."""

    program_name: str
    primary_languages: Sequence[str]
    support_email: str
    escalation_contact: str
    guardianship_review_cadence_weeks: int = 12

    def wallet_program(self) -> Sequence[WalletOption]:
        """Return wallet onboarding options tailored for parents."""

        return (
            WalletOption(
                name="Magic Link Wallet",
                category="custodial",
                provider="Magic",
                onboarding_steps=(
                    "Invite parents via SMS + email with localized copy",
                    "Collect minimal KYC (name, DOB, emergency contact)",
                    "Issue secure Magic link with 2FA bound to phone number",
                ),
                recovery_model="Guardian-assisted recovery through parent liaison desk with biometric hand-off at the campus.",
                support_channels=(
                    self.support_email,
                    "Parent Advisory Council liaison",
                    "24/7 Magic status page",
                ),
            ),
            WalletOption(
                name="Web3Auth Seedless Safe",
                category="semi-custodial",
                provider="Web3Auth",
                onboarding_steps=(
                    "Issue Web3Auth session with passkey enrollment in supported browsers",
                    "Pair wallet to Lil Footsteps Progressive Web App",
                    "Record guardian shard in encrypted custody vault",
                ),
                recovery_model="2-of-3 social recovery between parent, parent liaison, and Echo custody safe.",
                support_channels=(
                    self.support_email,
                    "Signal hotline: +1-917-ECHO-CARE",
                    "Walk-in tech support during pickup window",
                ),
            ),
            WalletOption(
                name="Gnosis Safe Community Vault",
                category="multi-sig",
                provider="Safe Global",
                onboarding_steps=(
                    "Collect provider verification",
                    "Enroll wallet in guardianship registry",
                    "Activate spending limits for childcare tuition disbursements",
                ),
                recovery_model="4-of-6 signer rotation reviewed every {weeks} weeks.".format(
                    weeks=self.guardianship_review_cadence_weeks
                ),
                support_channels=(
                    self.escalation_contact,
                    "Emergency bridge: emergency@echo.systems",
                ),
            ),
        )

    def credential_delivery(self) -> Sequence[CredentialChannel]:
        """Describe verifiable credential distribution channels."""

        return (
            CredentialChannel(
                label=f"{self.program_name} VC Wallet",
                medium="progressive_web_app",
                description="Branded VC wallet with push-to-refresh status, offline cache, and multi-language onboarding.",
                security_features=(
                    "Passkey authentication with biometric fallback",
                    "Encrypted storage (WebCrypto) with Secure Element on Android",
                    "Auto-expiring credentials with 90-day review",
                ),
                data_retention="No PII stored server-side; revocation list only keeps hashed credential IDs.",
            ),
            CredentialChannel(
                label="Custodial Credential Envelope",
                medium="email_pdf",
                description="Signed PDF credential with QR payload for parents who opt-out of web wallets.",
                security_features=(
                    "Time-boxed download links",
                    "Optional password delivered over SMS",
                    "Ledger entry mirrored in NonprofitBank logs",
                ),
                data_retention="PDF purge after 30 days; hashed receipt stored for audit.",
            ),
        )

    def provider_verification_protocol(self) -> QrAccessPolicy:
        """Return QR scanning policies for childcare provider front desks."""

        return QrAccessPolicy(
            scanner_role="Provider front desk or classroom lead",
            verification_steps=(
                "Scan parent's VC QR using provider mobile app",
                "Validate credential status + expiration via Echo API",
                "Log check-in with timestamp and classroom ID",
            ),
            offline_fallback="Fallback to shared passphrase + last 4 digits of parent phone when offline; sync later",
            audit_log="Encrypted daily export to Echo compliance safe with 30-day retention.",
        )

    def support_matrix(self) -> Mapping[str, Iterable[str]]:
        """Return human support matrix by language."""

        return {
            language: (
                "24/7 voicemail callback",
                "Signal channel staffed by parent liaison",
                "Monthly office hours with interpretation",
            )
            for language in self.primary_languages
        }

    def to_dict(self) -> Mapping[str, object]:
        """Serialise the toolkit into a dictionary for documentation or dashboards."""

        return {
            "program_name": self.program_name,
            "wallet_options": [asdict(option) for option in self.wallet_program()],
            "credential_channels": [asdict(channel) for channel in self.credential_delivery()],
            "provider_qr_policy": asdict(self.provider_verification_protocol()),
            "support_matrix": self.support_matrix(),
            "guardianship_review_cadence_weeks": self.guardianship_review_cadence_weeks,
        }


__all__ = [
    "WalletOption",
    "CredentialChannel",
    "QrAccessPolicy",
    "DigitalIdentityToolkit",
]
