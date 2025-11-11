# Configuring Required Status Checks

To ensure the build, security, and release workflows gate changes before they reach `main`, configure required status checks in the repository settings:

1. Navigate to **Settings → Branches** in the GitHub UI.
2. Under **Branch protection rules**, create or edit the rule that targets the `main` branch.
3. Enable **Require status checks to pass before merging**.
4. Add the following workflows as required checks:
   - `Build and Test / Unit tests (python)`
   - `Build and Test / Unit tests (typescript)`
   - `Build and Test / Unit tests (go)`
   - `Build and Test / Integration tests (python)`
   - `Build and Test / Integration tests (typescript)`
   - `Build and Test / Integration tests (go)`
   - `End-to-End / e2e (compose)`
   - `End-to-End / e2e (kind)`
   - `Security Safeguards / Generate SBOM`
   - `Security Safeguards / Vulnerability scanning`
   - `Security Safeguards / Policy enforcement`
5. Optionally require `Semantic Release / Semantic release and publish` if release promotion must succeed before merge.
6. Save the branch protection rule.

These checks ensure unit, integration, end-to-end, and security automation pass before pull requests are merged, and that releases are only produced from verified commits.
