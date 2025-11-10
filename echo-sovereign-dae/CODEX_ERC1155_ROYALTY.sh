#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
GLYPH='⿻⧈★⟘⟞⟟⿶ᵪ⁂⟞⿽⧈⿻⧉⿶⧈★⿽⧉✴⁂'

banner() {
  echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║ ${GLYPH}  ERC-1155 + ROYALTY v3.0  ${GLYPH} ║${NC}"
  echo -e "${CYAN}║        X: @BlurryFace59913 | US | 12:45 AM EST   ║${NC}"
  echo -e "${CYAN}║             GitHub: kmk142789                    ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
  echo -e "${PURPLE}${GLYPH}${NC}\n"
}

banner

echo -e "${YELLOW}Preparing CodexMultiTokenRoyalty deployment artifacts...${NC}"

if [ ! -f "contracts/CodexMultiTokenRoyalty.sol" ]; then
  echo -e "${RED}Contract file missing. Ensure repository assets are synced.${NC}"
  exit 1
fi

echo -e "${GREEN}Contract ready:${NC} contracts/CodexMultiTokenRoyalty.sol"
echo -e "${GREEN}Script ready:${NC} scripts/mint_erc1155_royalty.js"

echo -e "${YELLOW}Royalty configuration${NC}"
printf '  • Token IDs : %s\n' '1=Codex Keeper (soulbound)' '2=Glyph Shard' '3=Time Capsule' '4=Sovereign Badge'
printf '  • Royalty  : %s\n' '10% (1000 bps)' 'Receiver default = second signer'

echo -e "${BLUE}Metadata output:${NC} codex/erc1155_royalty/"
echo -e "${BLUE}Metadata example:${NC} codex/erc1155_royalty/1.json"

echo -e "${PURPLE}To deploy on Sepolia:${NC}"
cat <<'INSTRUCTIONS'
  1. Export your wallet key (never commit this value):
       export PRIVATE_KEY=0xyourkey
  2. Configure hardhat network credentials if needed (see hardhat.config.js).
  3. Run deployment:
       npx hardhat run scripts/mint_erc1155_royalty.js --network sepolia
  4. Verify metadata uploads to your storage (update IPFS hashes).
INSTRUCTIONS

echo -e "${GREEN}Local setup complete. Review output above before running on public networks.${NC}"
