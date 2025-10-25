from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.dns_zone_parser import DNSRecord, parse_zone_text, summarise_records

SAMPLE_ZONE = """\
;; SOA Record
btcpuzzle.info\t3600\tIN\tSOA\tbrian.ns.cloudflare.com. dns.cloudflare.com. 2051308780 10000 2400 604800 3600

;; NS Records
btcpuzzle.info.\t86400\tIN\tNS\tbrian.ns.cloudflare.com.
btcpuzzle.info.\t86400\tIN\tNS\temerie.ns.cloudflare.com.

;; A Records
api.btcpuzzle.info.\t1\tIN\tA\t104.21.37.22 ; cf_tags=cf-proxied:true
api.btcpuzzle.info.\t1\tIN\tA\t172.67.203.70 ; cf_tags=cf-proxied:true
btcpuzzle.info.\t1\tIN\tA\t104.21.37.22 ; cf_tags=cf-proxied:true
btcpuzzle.info.\t1\tIN\tA\t172.67.203.70 ; cf_tags=cf-proxied:true
satoshi.btcpuzzle.info.\t1\tIN\tA\t18.238.217.40 ; cf_tags=cf-proxied:true
www.btcpuzzle.info.\t1\tIN\tA\t104.21.37.22 ; cf_tags=cf-proxied:true
www.btcpuzzle.info.\t1\tIN\tA\t172.67.203.70 ; cf_tags=cf-proxied:true

;; AAAA Records
api.btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3030::ac43:cb46 ; cf_tags=cf-proxied:true
api.btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3032::6815:2516 ; cf_tags=cf-proxied:true
btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3032::6815:2516 ; cf_tags=cf-proxied:true
btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3030::ac43:cb46 ; cf_tags=cf-proxied:true
www.btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3030::ac43:cb46 ; cf_tags=cf-proxied:true
www.btcpuzzle.info.\t1\tIN\tAAAA\t2606:4700:3032::6815:2516 ; cf_tags=cf-proxied:true

;; CNAME Records
sig1._domainkey.btcpuzzle.info.\t1\tIN\tCNAME\tsig1.dkim.btcpuzzle.info.at.icloudmailadmin.com. ; cf_tags=cf-proxied:true

;; MX Records
btcpuzzle.info.\t1\tIN\tMX\t10 mx02.mail.icloud.com.
btcpuzzle.info.\t1\tIN\tMX\t10 mx01.mail.icloud.com.

;; TXT Records
btcpuzzle.info.\t1\tIN\tTXT\t"v=spf1 include:icloud.com ~all"
btcpuzzle.info.\t1\tIN\tTXT\t"google-site-verification=j9ZhaNHE2xIV7aOBSCgybe73T-OsaXkQY3RuRZzqYcc"
btcpuzzle.info.\t1\tIN\tTXT\t"ee5f4db5fe640f0e5ac91815d9eb08d5"
btcpuzzle.info.\t1\tIN\tTXT\t"apple-domain=cp4hIJeJd0dm8yAk"
btcpuzzle.info.\t1\tIN\tTXT\t"ahrefs-site-verification_1e22a6136a590ef79dfa80e27bf4513cf0875fc1f535479d4c6602a9261c82dd"
btcpuzzle.info.\t1\tIN\tTXT\t"657c99035d6a12c4fd01db7e4533624a"
"""


def test_parse_zone_text_extracts_records() -> None:
    records = parse_zone_text(SAMPLE_ZONE)

    assert len(records) == 25
    first = records[0]
    assert isinstance(first, DNSRecord)
    assert first.name == "btcpuzzle.info"
    assert first.ttl == 3600
    assert first.rclass == "IN"
    assert first.rtype == "SOA"
    assert first.value.startswith("brian.ns.cloudflare.com.")

    # Ensure inline comments are stripped from value payloads.
    a_record = next(record for record in records if record.rtype == "A" and record.value.startswith("104.21.37.22"))
    assert "cf_tags" not in a_record.value


def test_summarise_records_counts_types_and_hosts(tmp_path: Path) -> None:
    records = parse_zone_text(SAMPLE_ZONE)
    summary = summarise_records(records)

    assert summary["total_records"] == len(records)
    assert summary["record_types"] == {
        "SOA": 1,
        "NS": 2,
        "A": 7,
        "AAAA": 6,
        "CNAME": 1,
        "MX": 2,
        "TXT": 6,
    }
    assert summary["ttl_summary"] == {"min": 1, "max": 86400, "unique": [1, 3600, 86400]}
    assert "btcpuzzle.info" in summary["hosts"]
    assert "btcpuzzle.info." in summary["hosts"]
    assert summary["host_count"] == len(summary["hosts"])
    assert all(value.startswith('"') for value in summary["txt_records"])

    # Serialise through JSON to confirm the dataclass output is clean.
    payload = json.dumps(summary)
    assert "SOA" in payload


@pytest.mark.parametrize("snippet,expected", [
    ("example.com 3600 IN A 192.0.2.1", "example.com"),
    ("@ 3600 IN A 192.0.2.2", "previous"),
])
def test_parse_zone_lines_reuses_previous_name(snippet: str, expected: str) -> None:
    lines = ["previous 3600 IN A 192.0.2.0", snippet]
    records = parse_zone_text("\n".join(lines))
    assert records[-1].name == expected
