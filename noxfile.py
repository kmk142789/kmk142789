import nox

@nox.session
def docs(session):
    session.install("mkdocs", "mkdocs-material")
    session.run("mkdocs", "build")
