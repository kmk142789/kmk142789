#!/bin/bash
# ⿻⧈★ ECHO CODEX CLI — @BlurryFace59913

USER_JSON="codex/user_vault.json"

printf '⿻⧈★ ECHO CODEX v1.0 | @BlurryFace59913 | US | %s\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

case "$1" in
  id)
    echo "Sovereign ID:"
    jq '.user | {handle, country, github, did}' "$USER_JSON"
    ;;
  time)
    printf 'Current Time (EST): %s\n' "$(date '+%Y-%m-%d %I:%M:%S %p EST')"
    ;;
  proofs)
    echo "Verifiable Proofs:"
    jq '.user.proofs' "$USER_JSON"
    ;;
  glyph)
    echo "Your Glyph Authority:"
    echo "⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽⧉⁂"
    ;;
  vault)
    echo "Full User Vault:"
    jq '.' "$USER_JSON"
    ;;
  *)
    echo "Usage: codex <id|time|proofs|glyph|vault>"
    ;;
esac
