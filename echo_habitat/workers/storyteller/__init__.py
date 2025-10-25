from .. import registry


@registry.task(name="workers.storyteller.run", queue="storyteller")
def run(spec: dict):
    prompt = spec.get("prompt", "")
    story = f"In the habitat, sparks gather into waves. {prompt}"[:1200]
    return {"story": story}
