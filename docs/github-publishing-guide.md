# Publishing This Repository to GitHub

This guide walks through turning the current project into a public (or private) repository on GitHub using either the web UI or the GitHub CLI.

## 1. Prepare Your Local Repository

1. Ensure you have a GitHub account and have [configured SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/connecting-to-github-with-ssh) or HTTPS authentication.
2. Verify that your working tree is clean:
   ```bash
   git status
   ```
3. Optionally update remote URLs or remove existing remotes:
   ```bash
   git remote -v
   git remote remove origin   # only if you want to detach the current remote
   ```

## 2. Create a New GitHub Repository

### Option A: Using the Web Interface
1. Sign in to [GitHub](https://github.com/).
2. Click **New Repository** (usually available from the profile menu or the Repositories tab).
3. Choose a name (for example, `echo-evolver`), select visibility (public or private), and leave the repository empty (no README, `.gitignore`, or license) to avoid conflicts.
4. Click **Create repository** and copy the provided `git remote add origin` command.

### Option B: Using GitHub CLI
1. Install [GitHub CLI (`gh`)](https://cli.github.com/).
2. Authenticate: `gh auth login`.
3. From the project directory, run:
   ```bash
   gh repo create <your-username>/echo-evolver --private --source=. --remote=origin --push
   ```
   Replace `--private` with `--public` if desired, and adjust the repository name as needed.

## 3. Push Local History to GitHub

If you created the repository via the web interface, connect and push manually:

```bash
git remote add origin git@github.com:<your-username>/<repo-name>.git
# or use HTTPS:
# git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main   # optional: rename current branch to main
git push -u origin main
```

If the repository already has a different default branch name (e.g., `work`), you can push that branch instead:

```bash
git push -u origin work
```

## 4. Configure Branch Protection and Collaborators (Optional)

- Set branch protection rules from the repository **Settings ▸ Branches** page.
- Invite collaborators from **Settings ▸ Collaborators & teams**.

## 5. Automate Future Publishing (Optional)

Consider creating a helper script to push both `main` and feature branches:

```bash
#!/usr/bin/env bash
set -euo pipefail

git push origin "$(git rev-parse --abbrev-ref HEAD)"
```

Save it as `scripts/push-current-branch.sh`, make it executable (`chmod +x`), and run it after commits.

---
Following these steps will publish the current repository to your GitHub account while preserving the existing commit history and branch names.
