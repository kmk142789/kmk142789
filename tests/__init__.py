"""Ensure local test utilities are importable as a package.

Adding a module initializer prevents environment-level packages named
``tests`` from shadowing the repository's own test helpers when running
pytest directly from the working tree.
"""
