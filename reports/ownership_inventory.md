# KeyHunter / Echo Ownership Inventory

## Overview
- **GitHub account inspected:** [`kmk142789`](https://github.com/kmk142789)
- **Public repositories discovered:** 183 (GitHub REST API pages 1–2).
- **Organizations with visible membership:** none (GitHub REST API `/users/kmk142789/orgs`).
- **Analysis focus:** repositories and domains containing the strings `key`, `echo`, or `hunter`, plus the root repository that anchors the Echo project narrative.
- **Constraints:** unauthenticated GitHub API limited the inspection set to high-signal repositories (full 183 item audit would exceed the 60-requests/hour rate limit). Hosting-provider tokens were not provided. Direct DNS lookups and WHOIS queries were blocked by the execution environment (no outbound UDP/TCP 53, `whois` binary unavailable).

## 1. GitHub Discovery (high-signal subset)
Summary of the ten highest-signal repositories (full JSON in [`reports/data/github_key_echo_repos.json`](data/github_key_echo_repos.json)):

| Repository | Default branch | Head commit | Ownership markers present? | Keywords spotted | Domains referenced | Release assets |
| --- | --- | --- | --- | --- | --- | --- |
| `kmk142789/kmk142789` | `work` | `4db893c1e05e35ea0d2dde78d2afcb5c17d49c1b` | No OWNERS/CODEOWNERS/OWNERSHIP.md/RELEASE_PROVENANCE/forever_love.txt | “Our Forever Love” pervasive | — | None |
| `kmk142789/keyhunt` (fork) | `main` | `2134a2024e524775b13f82aa1fa07b1c8053f867` | None | None | GitHub mirrors, YouTube links | None |
| `kmk142789/KeyZero` (fork) | `main` | `b2d805000761d9b7cb41561ced3cedd99d6f4d2c` | None | None | `addresses.loyce.club`, CodeFactor | None |
| `kmk142789/BitcoinPrivateKeyHunter` (fork) | `master` | `09f78ad65cc25bea848b353714e7519938325f0f` | None | `KeyHunter` | — | None |
| `kmk142789/bitcoin-key-scanner` (fork) | `main` | `81b69305af6467ec89995583763851f0fa71f89e` | None | None | — | None |
| `kmk142789/echo-wallet` (fork) | `develop` | `a08e41a33054bd821d3def689a0de76739a1ccea` | None | None | PixelPlex/CI URLs | None |
| `kmk142789/echologic` (fork) | `master` | `ed8ec29951a4f91bec0d4fb8d40639cb9ce927d4` | None | “Echo” (project naming) | `echologic.org` | None |
| `kmk142789/echogarden` (fork) | `main` | `7a60d1b4ffc648495e431f4871fc8332e838eb66` | None | “Echo” | cloud provider docs | None |
| `kmk142789/echosocial` (fork) | `master` | `4fdaf9ec75f24ccac5e6931e6fe68d91159865c2` | None | “Echo” in upstream docs | Riseup/FSF domains | None |
| `kmk142789/echo-cas` (fork) | `master` | `3fc47a2704e113999673b983ce622e9320c25715` | None | None | — | None |
| `kmk142789/ScriptEchoDocs` (fork) | `master` | `790f537c7787e89dd1b042255b36a266c802eeb4` | None | “Echo” in documentation | `player.bilibili.com` | None |

### Commit authors (last 50 entries)
- `kmk142789/kmk142789`: `kmk142789 <blurryface142789420@gmail.com>`
- `kmk142789/keyhunt`: {Alberto/albertobsd@gmail.com, Vladimir Tarkhanov, mysterek1337, seega, Alexander, etc.}
- `kmk142789/KeyZero`: {vlnahp, gitpushoriginmaster, minhhieugma@gmail.com, SubGlitch1, 3subs, nikkdevic}
- `kmk142789/BitcoinPrivateKeyHunter`: {weshenshall@gmail.com, ajax000-ai}
- `kmk142789/bitcoin-key-scanner`: {ethicbrudhack <hacker001ethical@proton.me>}
- `kmk142789/echo-wallet`: {PixelPlex contributors (a.kosobuckiy@pixelplex.io, m.shautsou@pixelplex.io, etc.)}
- `kmk142789/echologic`: {Laszlo Papp <laszlo.papp@echologic.org>}
- `kmk142789/echogarden`: {Rotem Dan <rotemdan@gmail.com>}
- `kmk142789/echosocial`: {niklas@brueckenschlaeger.de, jrw@…, azul@riseup.net, juozas@hobo23}
- `kmk142789/echo-cas`: {matt@zukowski.ca, godfat@godfat.org, zeke@sikelianos.com, etc.}
- `kmk142789/ScriptEchoDocs`: {胡小根 <hxg@haomo-studio.com>, 王露雨 <wangluyu@haomo-studio.com>, 胡庆龙 <huqinglong@haomo-studio.com>, 谢俊豪 <xiejunhao@haomo-studio.com>}

> **Observation:** except for the root repository, the inspected projects are forks with no recent commits authored by `kmk142789`. Each lacks explicit ownership metadata (`OWNERS`, `CODEOWNERS`, `OWNERSHIP.md`, `RELEASE_PROVENANCE.json`, `forever_love.txt`).

### Keyword sweeps
- “KeyHunter” surfaced only in the upstream `BitcoinPrivateKeyHunter` README.
- “Echo” occurs throughout the Echo-related forks and the root project.
- “Our Forever Love” is unique to `kmk142789/kmk142789` (core Echo repo) and does not appear in the forks.

### README / config domain hints
- Only `echologic` surfaced a first-party-looking domain: **`echologic.org`**.
- Other URLs point to upstream GitHub repos, documentation portals, or third-party tooling (PixelPlex, Riseup, CodeFactor, OpenAI, etc.). No vercel.json/netlify.toml/dockerfiles declared custom deployments within the audited subset.

## 2. Package Registry Discovery
Searches against npm (`keyhunter`, `echo`, `maintainer:kmk142789`), Docker Hub (`keyhunter`, namespace `kmk142789`), and the GitHub Packages index returned **no packages** tied to the KeyHunter/Echo strings or the `kmk142789` publisher handle. PyPI does not offer an open JSON search endpoint without authentication; manual HTML parsing was skipped to avoid brittle scraping. No package artifacts can currently be claimed as “ours.”

## 3. Hosting / Deployments
Read-only API tokens for Vercel, Netlify, Render, or other hosting providers were not provided. Consequently, no deployment inventories could be fetched. There is no evidence (within repo configs) of linked Vercel/Netlify/Render projects that could be queried via public metadata alone.

## 4. Domains & DNS / WHOIS
- Candidate domains: `echologic.org` (from fork README). No Echo-specific domains surfaced in the root repo.
- DNS lookups (`dig echologic.org any +short`) failed because outbound DNS (UDP/TCP 53) is blocked inside the execution environment.
- WHOIS tooling is unavailable (`whois` command missing) and external TCP 43 is disallowed, preventing registrar or registrant-email verification.

## 5. Evidence Correlation & Confidence Ratings
| Artifact | Confidence (0–100) | Evidence highlights | Gaps / Next verification step |
| --- | --- | --- | --- |
| `github.com/kmk142789/kmk142789` | **90** | Direct control implied by repository ownership; commits authored by `kmk142789`; Echo narrative and “Our Forever Love” anchor throughout. | Add `CODEOWNERS` + `RELEASE_PROVENANCE.json` referencing key commits; publish signed release tag; prepare DNS TXT (`keyhunter-verify=<token>`) once canonical domain chosen. |
| `github.com/kmk142789/echologic` (fork) | 30 | Fork exists under account; upstream domain `echologic.org` referenced. No local commits. | Confirm intent: if ownership desired, add README section clarifying fork purpose; reach out to upstream maintainers; add provenance file only if project becomes active. |
| `github.com/kmk142789/echo-wallet` (fork) | 25 | Fork owned by account; upstream maintained by PixelPlex. | Determine whether this fork is active; if so, add `OWNERSHIP.md` stating stewardship; otherwise mark as archival fork. |
| `github.com/kmk142789/keyhunt`, `KeyZero`, `BitcoinPrivateKeyHunter`, `bitcoin-key-scanner`, `echogarden`, `echosocial`, `echo-cas`, `ScriptEchoDocs` | 10–20 | Passive forks with no local commits and no Echo branding. | Either archive or document fork purpose; no ownership claim without additional provenance. |
| Domain `echologic.org` | 20 | Mentioned in `echologic` README; no DNS/WHOIS confirmation. | Add DNS TXT: `keyhunter-verify=<new-token>` once registrar access confirmed; capture registrar support-ticket template requesting contact email update. |

### Recommended next actions
1. **Root repo provenance**
   - Add `CODEOWNERS` listing Josh / KeyHunter maintainers.
   - Generate `RELEASE_PROVENANCE.json` capturing SHA256 of release bundles.
   - Publish DNS TXT record (e.g., `keyhunter-verify=echo-2025-q4-root`) at the eventual canonical domain.
2. **Fork triage**
   - Decide which forks remain strategically important; add `OWNERSHIP.md` clarifying fork intent or archive to reduce noise.
   - For any fork adopted as first-party, replace upstream README with Echo-branded summary and add provenance metadata.
3. **Domain verification**
   - Contact `echologic.org` registrar (if under control) with support ticket: “Please add DNS TXT record `keyhunter-verify=<token>` for ownership attestation of the Echo project fork.”
   - If domain is not controlled, remove references or note lack of ownership in README.

### Support-ticket draft
> _Subject:_ Echo Project DNS TXT verification request
>
> _Body:_ “Hello, we administer the Echo project fork under the GitHub user `kmk142789`. Please add the DNS TXT record `keyhunter-verify=<token>` to `echologic.org` (or delegate access) so we can finalize provenance for the Echo ecosystem. Thank you.”

### Provenance pack manifest (filenames only)
Proposed ZIP structure for evidence collation:
```
provenance/
  github_api/repos_page1.json
  github_api/repos_page2.json
  github_api/orgs.json
  github_repos/key_echo_subset.json
  github_repos/kmk142789_commit_authors.txt
  github_repos/keyhunt_commit_authors.txt
  github_repos/KeyZero_commit_authors.txt
  github_repos/BitcoinPrivateKeyHunter_commit_authors.txt
  github_repos/bitcoin-key-scanner_commit_authors.txt
  github_repos/echo-wallet_commit_authors.txt
  github_repos/echologic_commit_authors.txt
  github_repos/echogarden_commit_authors.txt
  github_repos/echosocial_commit_authors.txt
  github_repos/echo-cas_commit_authors.txt
  github_repos/ScriptEchoDocs_commit_authors.txt
  screenshots/root_repo_our_forever_love.png
  logs/dig_echologic_org.txt
  logs/whois_echologic_org.txt
```

## Appendix: Data files
- [`reports/data/github_key_echo_repos.json`](data/github_key_echo_repos.json) — normalized snapshot of default branches, head commits, author lists, keyword hits, and domain references for the inspected repositories.
