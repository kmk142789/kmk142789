# Configuring Required Status Checks

To ensure that the new automation gates merges correctly, configure required status checks for the default branch.

## Prerequisites

- Repository administrator permissions.
- The workflows introduced in this change have already run at least once on the target branch so that GitHub can detect their names.

## Steps

1. Navigate to **Settings ▸ Branches** in the GitHub repository UI.
2. Under **Branch protection rules**, click **Add rule** (or edit the existing rule for `main`).
3. In **Branch name pattern**, enter `main` (or the branch you want to protect).
4. Enable **Require status checks to pass before merging**.
5. Click **Search for status checks in the last week** and add the following checks:
   - `Build and Test / Unit tests (python)`
   - `Build and Test / Unit tests (node)`
   - `Build and Test / Unit tests (go)`
   - `Build and Test / Integration tests (python)`
   - `Build and Test / Integration tests (node)`
   - `Build and Test / Integration tests (go)`
   - `End-to-End Verification / e2e-tests`
   - `Security and Compliance / security`
   - Any existing checks (linting, formatting, etc.) that must remain required.
6. (Optional) Enable **Require branches to be up to date before merging** to force merge commits to include the latest successful checks.
7. Save the rule.

After saving, GitHub will block merges until all required checks succeed, ensuring CI/CD, security, and end-to-end coverage remain enforced.
