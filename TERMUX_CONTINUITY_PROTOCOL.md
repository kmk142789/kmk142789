# 🔒 Continuity & Failover Execution Directive — Zero‑Downtime Termux Protocol (v2)

**Objective:** If Codex execution is constrained, development **must** continue immediately in Termux with **zero pause**, **zero redesign**, **zero loss of state**, and **zero deviation** from the active plan.

Execution continuity is mandatory. 🚀

---

## ✅ Absolute Continuity Guarantees (Non‑Negotiable)

1. **Termux = Codex parity (hard requirement)**
   - Provide a local Termux environment functionally equivalent to Codex.
   - **Priority order:** stability → persistence → reliability.

2. **Repository state is identical**
   - Same branch, same commit, same working tree.
   - No forks, no divergence, no shortcuts.

3. **Instant handoff**
   - Trigger: Codex limit reached.
   - Action: open Termux.
   - Result: immediate continuation at the exact same task state.

4. **Architecture and plan are immutable**
   - Contracts, specs, task order, and prior decisions are locked.
   - No reinterpretation, no rescoping, no drift.

---

## 1) 📦 Termux Setup — Copy/Paste (One‑Time)

> Run this once on the device. This installs the mandatory toolchain and creates a stable Python venv.

```bash
pkg update -y && pkg upgrade -y
pkg install -y \
  git \
  nodejs-lts \
  python \
  openssh \
  openssl \
  build-essential \
  make \
  clang \
  pkg-config \
  tmux

python -m venv ~/.venvs/codex
source ~/.venvs/codex/bin/activate
pip install -U pip setuptools wheel
```

### Optional (recommended) persistence hardening

```bash
pkg install -y termux-api
termux-wake-lock
```

---

## 2) 🔁 Repository Sync Commands (Exact Mirror)

> Replace the placeholders before running. These commands **guarantee** the Termux repo matches Codex exactly.

```bash
export CODEX_REPO_URL="<REPO_URL>"
export CODEX_BRANCH="<BRANCH_NAME>"
export CODEX_COMMIT="<COMMIT_SHA>"
export CODEX_DIR="$HOME/<REPO_DIR_NAME>"

# clone if missing
[ -d "$CODEX_DIR/.git" ] || git clone "$CODEX_REPO_URL" "$CODEX_DIR"

cd "$CODEX_DIR"

git fetch origin --prune

git checkout -B "$CODEX_BRANCH" "origin/$CODEX_BRANCH"

git reset --hard "$CODEX_COMMIT"

git clean -fdx
```

---

## 3) ⚡ Single‑Command Resume Work (Consolidated)

> This **single command set** resumes work in a persistent tmux session with full parity.

```bash
export CODEX_REPO_URL="<REPO_URL>"
export CODEX_BRANCH="<BRANCH_NAME>"
export CODEX_COMMIT="<COMMIT_SHA>"
export CODEX_DIR="$HOME/<REPO_DIR_NAME>"

[ -d "$CODEX_DIR/.git" ] || git clone "$CODEX_REPO_URL" "$CODEX_DIR"

tmux new -A -s codex "bash -lc '
  set -e
  cd "$CODEX_DIR"
  git fetch origin --prune
  git checkout -B "$CODEX_BRANCH" "origin/$CODEX_BRANCH"
  git reset --hard "$CODEX_COMMIT"
  git clean -fdx
  source ~/.venvs/codex/bin/activate
  exec "$SHELL"
'"
```

**Behavior:**
- If the tmux session exists, it resumes instantly.
- If it does not exist, it is created and initialized.
- The working tree is forced to the exact commit.

---

## 4) 🧠 Persistence Guarantee (Mandatory)

Required tmux characteristics:
- Session survives app backgrounding and device sleep.
- Session is network‑tolerant and battery‑safe.

Minimal verification:

```bash
tmux ls
```

If `codex` is listed, continuity is preserved.

---

## ✅ Success Condition

You can transition from **Codex → Termux in seconds** and continue building with **no observable difference** in workflow, state, or execution behavior.
