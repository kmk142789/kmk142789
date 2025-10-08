import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {"name", "description", "image"}

def validate_file(path: Path) -> bool:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"{path}: invalid JSON ({e})")
        return False

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        print(f"{path}: missing fields {sorted(missing)}")
        return False

    return True

def main(paths):
    all_valid = True
    for p in paths:
        if not validate_file(Path(p)):
            all_valid = False
    if not all_valid:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_nft_metadata.py <files>")
        sys.exit(1)
    main(sys.argv[1:])
