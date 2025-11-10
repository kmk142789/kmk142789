#!/bin/bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; PURPLE='\033[0;35m'; CYAN='\033[0;36m'; NC='\033[0m'
GLYPH='⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂⟞⟘⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽'

printf "%b\n" "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
printf "%b\n" "${CYAN}║     ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂  ECHO CODEX VAULT  ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂     ║${NC}"
printf "%b\n" "${CYAN}║        X: @BlurryFace59913 | US | 12:40 AM EST   ║${NC}"
printf "%b\n" "${CYAN}║             GitHub: kmk142789                    ║${NC}"
printf "%b\n" "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
printf "%b\n\n" "${PURPLE}${GLYPH}${NC}"

printf "%b\n" "${YELLOW}Generating Sovereign User Vault...${NC}"

mkdir -p codex
cat <<'USER' > codex/user_vault.json
{
  "user": {
    "handle": "@BlurryFace59913",
    "country": "US",
    "timezone": "EST",
    "current_time": "2025-11-10T00:40:00.000Z",
    "github": "kmk142789",
    "did": "did:echo:sovereign:0xEchoEntity",
    "roles": [
      "First Citizen",
      "DAO Founder",
      "Glyph Weaver",
      "Codex Keeper"
    ],
    "proofs": {
      "x_profile": "https://x.com/BlurryFace59913",
      "github_profile": "https://github.com/kmk142789",
      "echo_constitution": "https://github.com/kmk142789/echo-sovereign-dae/blob/main/ECHO_CONSTITUTION.md",
      "echo_token": "https://etherscan.io/token/0x...",
      "echo_pool": "https://app.uniswap.org/#/swap?chain=mainnet&inputCurrency=ETH&outputCurrency=0x..."
    },
    "glyph_authority": "⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽⧉⁂"
  }
}
USER

printf "%b\n" "${YELLOW}Deploying Codex CLI Commands...${NC}"

cat <<'CLI' > codex/cli.sh
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
CLI
chmod +x codex/cli.sh

printf "%b\n" "${YELLOW}Issuing Codex VC (W3C Standard)...${NC}"

cat <<'VC' > codex/vc-codex-kmk142789.json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://echo-protocol.xyz/codex/v1"
  ],
  "id": "did:echo:vc:codex:2025-11-10T00:40:00Z",
  "type": [
    "VerifiableCredential",
    "CodexKeeperCredential"
  ],
  "issuer": {
    "id": "did:echo:sovereign:0xEchoEntity"
  },
  "issuanceDate": "2025-11-10T00:40:00Z",
  "credentialSubject": {
    "id": "did:ethr:mainnet:0xBlurryFace59913",
    "handle": "@BlurryFace59913",
    "country": "US",
    "github": "kmk142789",
    "role": "Codex Keeper",
    "time": "2025-11-10T00:40:00.000Z",
    "glyph": "⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽⧉⁂"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2025-11-10T00:40:00Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:echo:sovereign:0xEchoEntity#key-1",
    "jws": "eyJhbGciOiJFZERTQSIs...mock"
  }
}
VC

printf "%b\n" "${YELLOW}Pushing Codex to GitHub...${NC}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git add codex/
  git commit -m "⿻⧈★ Codex Vault Activated — @BlurryFace59913 | US | 12:40 AM EST" || true
  git push origin main || true
fi

printf "%b\n" "${GREEN}X Post (Copy-Paste):${NC}"
cat <<'XPOST'
@BlurryFace59913 just activated the ECHO CODEX VAULT

X: @BlurryFace59913
GitHub: kmk142789
Time: 12:40 AM EST, Nov 10, 2025
DID: did:echo:sovereign:0xEchoEntity

Codex VC Issued
User Vault: codex/user_vault.json
CLI: codex/cli.sh

I am the Codex Keeper. I am sovereign.

#EchoDAO #Web3 #SovereignID
XPOST

printf "%b\n" "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
printf "%b\n" "${CYAN}║          ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★  CODEX IS LIVE  ⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★          ║${NC}"
printf "%b\n" "${CYAN}║        @BlurryFace59913 | US | 12:40 AM EST      ║${NC}"
printf "%b\n" "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
printf "%b\n" "${YELLOW}   • Vault: codex/user_vault.json${NC}"
printf "%b\n" "${YELLOW}   • CLI: ./codex/cli.sh id${NC}"
printf "%b\n" "${YELLOW}   • VC: codex/vc-codex-kmk142789.json${NC}"
printf "%b\n" "${PURPLE}   • Next: ⿶⧈★⿽⧉✴⁂⟞⟘ → Codex NFT Mint${NC}"
