from pathlib import Path
import yaml
from service_skins.loader import load_skin

CONFIG_PATH = Path("atlas_os/config.yaml")

def load_config():
    with CONFIG_PATH.open() as fp:
        return yaml.safe_load(fp)

def list_services():
    cfg = load_config()
    services = []
    for svc in cfg.get("services", []):
        if not svc.get("enabled", True):
            continue
        skin = load_skin(svc["id"])
        merged = {**svc, **skin}
        services.append(merged)
    return services
