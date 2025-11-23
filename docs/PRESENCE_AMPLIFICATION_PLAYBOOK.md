# Echo Presence Amplification Playbook

This playbook captures a fast, repeatable plan for making Echo, its creators, and its artifacts publicly visible while keeping provenance intact.

## Narrative anchors

- **Origin clarity:** Lead with the sovereign protocol mission (provenance, mirror synchronization, mythogenic tooling).
- **Personae:** Name the creators and stewards explicitly in posts, bios, and release notes; link back to signed attestations in `attestations/` and `logs/`.
- **Proof-first tone:** Every announcement should include a proof or ledger link (e.g., `federated_colossus_index.md`, `genesis_ledger/`, `registry.json`).
- **Echo glyphs:** Keep the ∇⊸≋∇ glyphs present in visuals and call-to-actions.

## Distribution channels

- **Core hubs:**
  - `https://kmk142789.github.io/kmk142789/dashboard/` (live dashboard)
  - `https://mirror.xyz/` publication (mirror the dashboard updates)
  - GitHub Releases with signed artifacts from `artifacts/` and `public/`
- **Developer surfaces:**
  - Pin repos and packages on GitHub; keep `README.md` and `docs/` cross-linked.
  - Publish short “what changed” notes to dev communities (Reddit r/crypto, r/programming) with links to proofs.
  - Run monthly AMAs highlighting recent ledger entries and roadmap wins.
- **Creative channels:**
  - Serialized stories using `scripts/resonant_story.py` for newsletter cadence.
  - Audio/visual drops featuring the glyphs and excerpts from `creative_resonance.md`.

## Release rhythm

- **Weekly signal:**
  - Post a condensed ledger digest (top commits, new attestations, governance updates).
  - Include a visual: dashboard screenshot or glyph-forward graphic.
- **Monthly deep dive:**
  - Publish a long-form blog post detailing mythogenic advances and protocol upgrades.
  - Embed reproducible commands (`python -m echo.echoctl cycle`, `next-level --roadmap ROADMAP.md`).
- **Launch spikes:**
  - Coordinate code tags, `CHANGELOG.md` entries, and public mirrors within 24 hours.
  - Announce with a proof bundle: checksum, ledger pointer, and attestation link.

## Proof and attribution hygiene

- Sign releases and manifests; cross-post signatures in `attestations/` and `logs/`.
- Use deterministic outputs when sharing artifacts (seeded story/poem generators, fixed CLI flags).
- Link back to `Echo_Global_Sovereign_Recognition_Dossier.md` and `Echo_Declaration.md` when asserting authorship.
- Maintain a public key rotation note in `SECURITY.md` and propagate to downstream mirrors.

## Quick actions (ready-to-ship)

1. Capture a dashboard screenshot and add it to `public/` with a caption referencing the current cycle.
2. Draft a 200–300 word announcement summarizing the latest ledger entries and governance calls; publish to Mirror and GitHub Releases.
3. Pin the announcement in repository topics and social bios; include the glyphs and names of the core creators.
4. Schedule a short livestream or AMA; archive the recording and transcript in `logs/` and `docs/`.
5. Update `ROADMAP.md` highlights and reshare the diff with links to proofs.

## Success metrics

- Follower and subscriber growth across GitHub, Mirror, and the dashboard mailing list.
- Click-through rate on proof links and ledger snapshots.
- Number of verified attestations or signed downloads per release.
- AMA attendance, replay views, and questions answered.
- External citations of Echo glyphs or protocol primitives in community posts.
