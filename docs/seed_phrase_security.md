# Seed Phrase Security Guidelines

Seed phrases (also known as mnemonic recovery phrases) are extremely sensitive secrets. Anyone with access to a valid seed phrase can permanently control the associated accounts and assets. To protect participants in this project and the wider ecosystem, **do not store, transmit, or replicate seed phrases in this repository or any shared channel**.

## Handling Principles

1. **Never commit real seed phrases.** Treat every seed phrase as production-critical data. If you need a seed for development, generate an obvious dummy phrase such as "abandon" repeated 12 times and clearly label it as test-only.
2. **Use environment variables and secret managers.** When integration or testing requires a mnemonic, load it from a local `.env` file or secure vault that is excluded from version control.
3. **Scrub logs and diagnostics.** Double-check that automated tooling (CI logs, screenshots, crash dumps) does not capture or echo seed phrases.
4. **Rotate credentials after exposure.** If a real seed phrase is ever shared inappropriately, immediately migrate affected funds, derive new keys, and revoke the compromised seed.
5. **Educate contributors.** Ensure every collaborator understands the irreversible risk posed by leaked mnemonics and reviews these guidelines before submitting code.

## Repository Hygiene Checklist

- [ ] `.gitignore` excludes files that might contain secrets (e.g., `.env`, backup exports).
- [ ] Tests use deterministic, fake mnemonics generated on the fly.
- [ ] Documentation includes only illustrative examples and clearly marks them as non-functional.
- [ ] Code reviews flag any addition that resembles a real seed phrase or private key.

By following these practices we keep contributors safe and respect the irreversible nature of seed phrase compromise.
