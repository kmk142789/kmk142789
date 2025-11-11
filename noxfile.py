import nox

@nox.session
def docs(session):
    session.install("mkdocs", "mkdocs-material", "pyyaml")
    session.run("python", "scripts/generate_doc_assets.py")
    session.run("mkdocs", "build")
