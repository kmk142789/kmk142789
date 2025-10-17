"""Echo Atlas: persistent identity and network map utilities."""

__all__ = ["AtlasService"]


def __getattr__(name: str):
    if name == "AtlasService":
        from .service import AtlasService

        return AtlasService
    raise AttributeError(name)
