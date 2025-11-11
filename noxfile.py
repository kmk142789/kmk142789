import nox


CORE_DEPS = [
    "numpy>=1.24",
    "pydantic>=2.6",
    "rich>=13",
    "cryptography>=41",
    "pandas>=2.1",
    "streamlit>=1.32",
    "typer>=0.9",
    "matplotlib>=3.8",
    "jsonschema>=4.20",
    "fastapi>=0.110",
    "starlette>=0.37",
]


@nox.session
def docs(session):
    session.install("mkdocs", "mkdocs-material")
    session.run("mkdocs", "build")


@nox.session
def tests(session):
    session.install("pytest")
    session.install(*CORE_DEPS)
    session.install("-r", "requirements.txt")
    session.install("-r", "atlas_os/requirements.txt")
    session.env["PYTHONPATH"] = "."
    session.env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    session.run("pytest", "tests", "atlas_os/atlas_runtime/tests", "-q")


@nox.session
def compliance(session):
    session.install(*CORE_DEPS)
    session.install("-r", "requirements.txt")
    session.env["PYTHONPATH"] = "."
    session.run("python", "-m", "compliance.cli", "asterc:validate", "identity")
