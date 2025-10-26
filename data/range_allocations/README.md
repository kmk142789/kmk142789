# Range Allocations

This directory stores curated key-search windows for unresolved Bitcoin puzzle
keys.  Each file lists inclusive hexadecimal start:end pairs that span exactly
2^36 values (0x1_0000_0000).  The windows are designed for use with Keyhunt and
similar distributed search tooling where contributors claim non-overlapping
segments.

## Files

- `puzzle66_72bit_ranges.txt` — Historical sweep coverage provided by Echo for
  the 72-bit search around Puzzle #66.
- `puzzle67_72bit_ranges.txt` — Community-sourced coverage for the next batch of
  72-bit spans that target Puzzle #67.

As with other archival datasets in this repository, updates are append-only and
should go through the normal review process to preserve provenance.
