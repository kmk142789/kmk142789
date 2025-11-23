import textwrap

from echo_cli.workspace_admin import (
    AdminSettingsPayload,
    AdminSsoConfig,
    EmailRoutingRule,
    GatewayConfig,
    build_atom_entry,
    render_gateway_payload,
    render_routing_payload,
    render_sso_payload,
    summarize_payloads,
)


def _strip(text: str) -> str:
    return textwrap.dedent(text).strip()


def test_build_atom_entry_preserves_property_order():
    xml = build_atom_entry([("first", "1"), ("second", "2")])
    assert xml == _strip(
        """
        <atom:entry xmlns:atom='http://www.w3.org/2005/Atom'
          xmlns:apps='http://schemas.google.com/apps/2006'>
          <apps:property name='first' value='1' />
          <apps:property name='second' value='2' />
        </atom:entry>
        """
    )


def test_render_sso_payload_matches_workspace_feed():
    payload = render_sso_payload(
        "example.com",
        AdminSsoConfig(
            saml_signon_uri="https://idp.example.com/login",
            saml_logout_uri="https://idp.example.com/logout",
            change_password_uri="https://idp.example.com/change",
            enable_sso=True,
            sso_whitelist="10.0.0.0/8",
            use_domain_specific_issuer=False,
        ),
    )
    assert isinstance(payload, AdminSettingsPayload)
    assert payload.method == "PUT"
    assert payload.url.endswith("example.com/sso/general")
    assert "samlSignonUri" in payload.xml
    assert "enableSSO" in payload.xml
    assert "ssoWhitelist" in payload.xml


def test_render_gateway_payload_supports_tls_mode():
    payload = render_gateway_payload(
        "example.com",
        GatewayConfig(smart_host="smtp.out.example.com", smtp_mode="SMTP_TLS"),
    )
    assert payload.method == "PUT"
    assert payload.url.endswith("/email/gateway")
    assert "SMTP_TLS" in payload.xml


def test_render_routing_payload_describes_delivery_strategy():
    payload = render_routing_payload(
        "example.com",
        EmailRoutingRule(
            route_destination="smtp.in.example.com",
            route_rewrite_to=False,
            route_enabled=True,
            bounce_notifications=True,
            account_handling="allAccounts",
        ),
    )
    assert payload.method == "POST"
    assert "emailrouting" in payload.url
    assert "routeDestination" in payload.xml
    assert "accountHandling" in payload.xml


def test_summarize_payloads_round_trips_core_fields():
    payloads = [
        render_sso_payload(
            "example.com",
            AdminSsoConfig(
                saml_signon_uri="https://idp.example.com/login",
                saml_logout_uri="https://idp.example.com/logout",
                change_password_uri="https://idp.example.com/change",
            ),
        ),
        render_gateway_payload("example.com", GatewayConfig(smart_host="smtp.out.example.com")),
    ]
    summaries = summarize_payloads(payloads)
    assert isinstance(summaries, list)
    assert all("url" in summary for summary in summaries)
    assert all("xml" in summary for summary in summaries)

