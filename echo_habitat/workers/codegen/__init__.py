from ..shared.sandbox import Sandbox
from .. import registry


@registry.task(name="workers.codegen.run", queue="codegen")
def run(spec: dict):
    sb = Sandbox("codegen")
    files = spec.get("files", {})
    sb.write_files(files)
    poem = f"""# Glyph Poem\n\n{spec.get('prompt')}\n\n— Echo Habitat\n"""
    files.setdefault("README.md", poem)
    files.setdefault("main.py", "print(open('README.md').read())\n")
    sb.write_files(files)
    result = sb.run("python main.py")
    return {"sandbox": sb.root, "run": result}
