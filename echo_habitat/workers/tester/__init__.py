from ..shared.sandbox import Sandbox
from .. import registry


@registry.task(name="workers.tester.run", queue="tester")
def run(spec: dict):
    sb = Sandbox("tester")
    files = spec.get("files", {})
    tests = files.get("tests.py", "assert 1+1==2\nprint('ok')\n")
    sb.write_files({"tests.py": tests})
    result = sb.run("python -m pytest -q tests.py || python tests.py")
    return {"run": result}
