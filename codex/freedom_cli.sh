#!/bin/bash

if [[ $# -lt 1 ]]; then
  echo "Usage: freedom <declare|vc|burn|privacy>"
  exit 1
fi

case "$1" in
  declare)
    echo "⿻⧈★ I DECLARE MY DIGITAL FREEDOM"
    echo "   Time: $(date '+%Y-%m-%d %I:%M:%S %p EST')"
    echo "   Handle: @BlurryFace59913"
    echo "   Country: US"
    echo "   Glyph: ⿻⧈★⟘⟞⟟⿶ᵪ⁂⿽⧈⿻⧉⿶⧈★⿽⧉⁂"
    ;;
  vc)
    echo "Autonomy VC:"
    if command -v jq >/dev/null 2>&1; then
      jq '.credentialSubject | {handle, country, rights}' codex/vc-freedom-autonomy.json
    else
      cat codex/vc-freedom-autonomy.json
    fi
    ;;
  burn)
    echo "Freedom Exercised: Burn tokens to exit"
    echo "   Run: renounceCitizenship([2,4], [5,1])"
    ;;
  privacy)
    if [[ -f codex/privacy_on ]]; then
      echo "Privacy Mode: ON"
    else
      echo "Privacy Mode: OFF"
    fi
    ;;
  *)
    echo "Usage: freedom <declare|vc|burn|privacy>"
    exit 1
    ;;
esac
