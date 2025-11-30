from typing import Callable, Dict
import importlib

registry: Dict[str, Callable] = {}


def register(name: str):
    def _wrap(fn):
        registry[name] = fn
        return fn

    return _wrap


def load(name: str) -> Callable:
    if name not in registry:
        raise ValueError(f"Unknown service pack {name}")
    return registry[name]
