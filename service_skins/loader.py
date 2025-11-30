import yaml
from pathlib import Path

SKINS_DIR = Path("service_skins")


def load_skin(skin_id: str) -> dict:
    path = SKINS_DIR / f"{skin_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Skin '{skin_id}' not found")
    with path.open() as fp:
        return yaml.safe_load(fp)


def list_skins():
    skins = []
    for f in SKINS_DIR.glob("*.yaml"):
        with f.open() as fp:
            skins.append(yaml.safe_load(fp))
    return skins
