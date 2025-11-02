from __future__ import annotations

from codex.registry_builder import PullRequestRecord, generate_markdown


def test_pull_request_record_from_api_normalizes_fields() -> None:
    payload = {
        "number": 42,
        "title": "Add Echo puzzle module",
        "body": "## Summary\nAdds a new puzzle pipeline.\n\nFixes #123 and closes owner/repo#99.",
        "merge_commit_sha": "abc123def456",
        "merged_at": "2024-05-01T12:34:56Z",
        "html_url": "https://github.com/owner/repo/pull/42",
    }

    record = PullRequestRecord.from_api(payload)

    assert record.summary == "Summary"
    assert record.linkedIssues == ["#123", "owner/repo#99"]
    assert record.commitHash == "abc123def456"
    assert record.timestamp == "2024-05-01T12:34:56Z"


def test_generate_markdown_builds_table_and_issue_index() -> None:
    record = PullRequestRecord(
        id=7,
        title="Integrate EchoOS telemetry",
        summary="Add telemetry stream",
        linkedIssues=["#1", "#2"],
        commitHash="deadbeefcafebabe",
        timestamp="2024-06-02T00:00:00Z",
        url="https://github.com/owner/repo/pull/7",
    )

    manifest = {"repository": "owner/repo", "generatedAt": "2024-06-02T01:23:45Z"}
    markdown = generate_markdown([record], manifest)

    assert "| [7](https://github.com/owner/repo/pull/7) |" in markdown
    assert "## Linked Issues" in markdown
    assert "- #1: #7" in markdown
