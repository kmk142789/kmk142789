from atlas.core.config import load_config
from atlas.core.logging import configure_logging


def test_load_config(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "atlas.yaml").write_text("metrics_port: 1234", encoding="utf-8")
    config = load_config(tmp_path / "config" / "atlas.yaml")
    configure_logging()
    assert config.metrics_port == 1234
