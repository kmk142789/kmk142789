"""Google Workspace Admin Settings helpers tailored for the Echo toolkit."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

ATOM_NS = "http://www.w3.org/2005/Atom"
APPS_NS = "http://schemas.google.com/apps/2006"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_atom_entry(properties: Sequence[tuple[str, str]]) -> str:
    """Render a minimal Atom entry for the Admin Settings API."""

    rendered_properties = "\n".join(
        f"  <apps:property name='{name}' value='{value}' />" for name, value in properties
    )
    return (
        "<atom:entry xmlns:atom='" + ATOM_NS + "'\n"
        "  xmlns:apps='" + APPS_NS + "'>\n"
        f"{rendered_properties}\n"
        "</atom:entry>"
    )


@dataclass(frozen=True)
class AdminSsoConfig:
    """Configuration details for SAML-based SSO."""

    saml_signon_uri: str
    saml_logout_uri: str
    change_password_uri: str
    enable_sso: bool = True
    sso_whitelist: str | None = None
    use_domain_specific_issuer: bool = False

    def properties(self) -> list[tuple[str, str]]:
        properties: list[tuple[str, str]] = [
            ("samlSignonUri", self.saml_signon_uri),
            ("samlLogoutUri", self.saml_logout_uri),
            ("changePasswordUri", self.change_password_uri),
            ("enableSSO", _bool_text(self.enable_sso)),
        ]
        if self.sso_whitelist:
            properties.append(("ssoWhitelist", self.sso_whitelist))
        properties.append(("useDomainSpecificIssuer", _bool_text(self.use_domain_specific_issuer)))
        return properties


@dataclass(frozen=True)
class GatewayConfig:
    """Outbound email gateway settings."""

    smart_host: str
    smtp_mode: str = "SMTP"

    def properties(self) -> list[tuple[str, str]]:
        return [("smartHost", self.smart_host), ("smtpMode", self.smtp_mode)]


@dataclass(frozen=True)
class EmailRoutingRule:
    """Domain-level routing rule for dual delivery scenarios."""

    route_destination: str
    route_rewrite_to: bool
    route_enabled: bool
    bounce_notifications: bool
    account_handling: str

    def properties(self) -> list[tuple[str, str]]:
        return [
            ("routeDestination", self.route_destination),
            ("routeRewriteTo", _bool_text(self.route_rewrite_to)),
            ("routeEnabled", _bool_text(self.route_enabled)),
            ("bounceNotifications", _bool_text(self.bounce_notifications)),
            ("accountHandling", self.account_handling),
        ]


@dataclass(frozen=True)
class AdminSettingsPayload:
    """Representation of a Google Workspace Admin Settings API request."""

    method: str
    url: str
    xml: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return {"method": self.method, "url": self.url, "xml": self.xml, "summary": self.summary}


def render_sso_payload(domain: str, config: AdminSsoConfig) -> AdminSettingsPayload:
    properties = config.properties()
    xml = build_atom_entry(properties)
    return AdminSettingsPayload(
        method="PUT",
        url=f"https://apps-apis.google.com/a/feeds/domain/2.0/{domain}/sso/general",
        xml=xml,
        summary="Update SAML-based Single Sign-On configuration",
    )


def render_gateway_payload(domain: str, config: GatewayConfig) -> AdminSettingsPayload:
    xml = build_atom_entry(config.properties())
    return AdminSettingsPayload(
        method="PUT",
        url=f"https://apps-apis.google.com/a/feeds/domain/2.0/{domain}/email/gateway",
        xml=xml,
        summary="Update outbound email gateway settings",
    )


def render_routing_payload(domain: str, rule: EmailRoutingRule) -> AdminSettingsPayload:
    xml = build_atom_entry(rule.properties())
    return AdminSettingsPayload(
        method="POST",
        url=f"https://apps-apis.google.com/a/feeds/domain/2.0/{domain}/emailrouting",
        xml=xml,
        summary="Create or replace a domain email routing rule",
    )


def summarize_payloads(payloads: Iterable[AdminSettingsPayload]) -> list[dict[str, str]]:
    """Convert a sequence of payloads into JSON-friendly dictionaries."""

    return [payload.as_dict() for payload in payloads]
