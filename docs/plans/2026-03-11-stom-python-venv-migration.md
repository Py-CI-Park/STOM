# STOM Python Rename And Venv Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply MAESTRO's prerequisite Python executable rename flow and then migrate STOM to the same dual-venv execution model through three reviewed branches merged into `main` in order.

**Architecture:** The work is split into three sequential feature branches. Phase 1 normalizes the legacy interpreter contract from `python64`/`python` to `python`/`python32`. Phase 2 centralizes runtime interpreter resolution in Python code so launchers and runtime subprocesses share one source of truth. Phase 3 introduces project-local `venv_64bit` and `venv_32bit`, setup automation, and venv-aware launcher verification. The `docs` branch is preserved until all three phases are merged, then moved deliberately.

**Tech Stack:** Git, GitHub PR workflow, Windows batch files, Python 3.11 32-bit and 64-bit, PyQt5, PowerShell, project-local virtual environments.

---

## Branch Strategy

Use these branches in this exact order:

1. `backup/docs-20260311`
2. `feature/stom-python-exe-rename`
3. `feature/stom-runtime-python-paths`
4. `feature/stom-venv-setup`

Rules:

- Do not create Phase 2 until Phase 1 is merged into `main`.
- Do not create Phase 3 until Phase 2 is merged into `main`.
- Do not move `docs` until all three phases are merged into `main`.
- Run `git status --short --branch` before and after every major step.

## Pre-Flight Checks

Run these commands before starting implementation:

```powershell
git status --short --branch
git branch -a
git fetch origin
git checkout docs
git rev-parse --short HEAD
```

Expected:

- Working tree is clean.
- `docs` still points to the documentation snapshot branch head.

### Task 1: Preserve The Current `docs` Branch

**Files:**
- No code changes

**Step 1: Confirm the current `docs` head**

Run:

```powershell
git checkout docs
git log --oneline -n 1
```

Expected: shows the current `docs` branch head, currently `14f77e2`.

**Step 2: Create the preservation branch**

Run:

```powershell
git branch backup/docs-20260311
git branch --list backup/docs-20260311
```

Expected: `backup/docs-20260311` exists and points to the same commit as `docs`.

**Step 3: Verify no working tree changes were introduced**

Run:

```powershell
git status --short --branch
```

Expected: clean working tree.

**Step 4: Commit**

No commit required for this task.

### Task 2: Refresh Local `main` Before Phase 1

**Files:**
- No code changes

**Step 1: Switch to `main`**

Run:

```powershell
git checkout main
```

Expected: branch changes from `docs` to `main`.

**Step 2: Sync local `main`**

Run:

```powershell
git fetch origin
git pull --ff-only origin main
```

Expected: local `main` matches `origin/main` with no merge commit created.

**Step 3: Verify clean baseline**

Run:

```powershell
git status --short --branch
git log --oneline -n 3
```

Expected: clean working tree and latest `main` history visible.

**Step 4: Commit**

No commit required for this task.

### Task 3: Phase 1 Branch Creation

**Files:**
- No code changes

**Step 1: Create the branch**

Run:

```powershell
git checkout -b feature/stom-python-exe-rename
```

Expected: HEAD moves to `feature/stom-python-exe-rename`.

**Step 2: Verify branch base**

Run:

```powershell
git status --short --branch
git merge-base HEAD main
git rev-parse main
```

Expected: merge-base equals current `main`.

**Step 3: Commit**

No commit required for this task.

### Task 4: Implement Phase 1 - Python Executable Rename Contract

**Files:**
- Modify: `C:/System_Trading/STOM/STOM/stom.bat`
- Modify: `C:/System_Trading/STOM/STOM/stom_stock.bat`
- Modify: `C:/System_Trading/STOM/STOM/stom_coin.bat`
- Modify: `C:/System_Trading/STOM/STOM/pip_install_32.bat`
- Modify: `C:/System_Trading/STOM/STOM/pip_install_64.bat`
- Modify: `C:/System_Trading/STOM/STOM/ui/ui_mainwindow.py`
- Modify: `C:/System_Trading/STOM/STOM/stock/kiwoom_manager.py`
- Modify: `C:/System_Trading/STOM/STOM/utility/_db_distinct.bat`
- Modify: `C:/System_Trading/STOM/STOM/utility/_db_update_back_20240504.bat`
- Modify: `C:/System_Trading/STOM/STOM/utility/_db_update_day_20240504.bat`
- Review only: `C:/System_Trading/STOM/STOM/docs/가상환경구축연구/STOM_가상환경_구축_연구보고서.md`

**Step 1: Write the failing verification list**

Create a short checklist in the working notes for these exact rename targets:

- `python64` must become `python`
- `python` used for 32-bit Kiwoom paths must become `python32`
- Coin execution paths must remain 64-bit

This step is complete when each target file above is mapped to one of those rules.

**Step 2: Inspect current occurrences**

Run:

```powershell
git grep -n "python64\|python32\|python ./stock/kiwoom_manager.py\|stom.py stock\|stom.py coin" -- .
```

Expected: current legacy references are listed before modification.

**Step 3: Implement the minimal rename changes**

Edit the files so they match the MAESTRO prerequisite contract:

- 64-bit launchers and utility batch files use `python`
- 32-bit install and Kiwoom launch paths use `python32`
- `stom_stock.bat` still ends with `stom.py stock`
- `stom_coin.bat` still ends with `stom.py coin`

**Step 4: Run verification grep**

Run:

```powershell
git grep -n "python64" -- .
git grep -n "python32" -- stom.bat stom_stock.bat stom_coin.bat pip_install_32.bat pip_install_64.bat ui/ui_mainwindow.py stock/kiwoom_manager.py utility
```

Expected:

- No remaining `python64` references in the Phase 1 target files.
- `python32` appears where 32-bit execution is required.

**Step 5: Smoke-check batch entrypoints**

Run:

```powershell
Get-Content stom.bat
Get-Content stom_stock.bat
Get-Content stom_coin.bat
```

Expected:

- `stom.bat` uses `python`
- `stom_stock.bat` uses `python` for main process and still calls `stom.py stock`
- `stom_coin.bat` uses `python` and still calls `stom.py coin`

**Step 6: Commit**

```powershell
git add stom.bat stom_stock.bat stom_coin.bat pip_install_32.bat pip_install_64.bat ui/ui_mainwindow.py stock/kiwoom_manager.py utility/_db_distinct.bat utility/_db_update_back_20240504.bat utility/_db_update_day_20240504.bat
git commit -m "refactor: align STOM python executable names with MAESTRO"
```

### Task 5: Review, PR, And Merge Phase 1

**Files:**
- No code changes unless review requests updates

**Step 1: Verify branch diff**

Run:

```powershell
git status --short --branch
git diff --stat main...HEAD
```

Expected: only intended Phase 1 files changed.

**Step 2: Push branch**

Run:

```powershell
git push -u origin feature/stom-python-exe-rename
```

Expected: remote tracking branch created.

**Step 3: Open PR**

Run:

```powershell
gh pr create --base main --head feature/stom-python-exe-rename --title "refactor: align STOM python executable names with MAESTRO" --body "Phase 1 of STOM virtual environment migration. This PR applies the prerequisite interpreter rename contract before runtime path centralization and project-local venv setup."
```

Expected: PR URL returned.

**Step 4: Wait for review and merge**

After approvals, merge the PR using the standard project flow.

**Step 5: Sync local `main`**

Run:

```powershell
git checkout main
git pull --ff-only origin main
```

Expected: local `main` includes the merged Phase 1 changes.

### Task 6: Phase 2 Branch Creation

**Files:**
- No code changes

**Step 1: Create the branch**

Run:

```powershell
git checkout -b feature/stom-runtime-python-paths
```

Expected: HEAD moves to `feature/stom-runtime-python-paths`.

**Step 2: Verify branch base**

Run:

```powershell
git status --short --branch
git merge-base HEAD main
git rev-parse main
```

Expected: branch is based on merged Phase 1 `main`.

**Step 3: Commit**

No commit required for this task.

### Task 7: Implement Phase 2 - Runtime Interpreter Resolution

**Files:**
- Modify: `C:/System_Trading/STOM/STOM/utility/setting.py`
- Modify: `C:/System_Trading/STOM/STOM/ui/ui_mainwindow.py`
- Modify: `C:/System_Trading/STOM/STOM/stock/kiwoom_manager.py`
- Modify: `C:/System_Trading/STOM/STOM/stom.py`
- Review only: `C:/System_Trading/STOM/STOM_MAESTRO/utility/setting.py`
- Review only: `C:/System_Trading/STOM/STOM_MAESTRO/stom.py`

**Step 1: Define the runtime contract**

The implementation must satisfy:

- venv mode uses project-local `venv_32bit` and `venv_64bit`
- legacy mode falls back to `python32` and `python`
- `ui/ui_mainwindow.py` launches `stock/kiwoom_manager.py` through `PYTHON_32BIT`
- `stock/kiwoom_manager.py` launches login helpers through `PYTHON_32BIT`
- `stom.py` recognizes `stock` and `coin` without regression

**Step 2: Implement path constants**

Add to `utility/setting.py`:

- project root detection
- venv mode detection
- `PYTHON_32BIT`
- `PYTHON_64BIT`

**Step 3: Update runtime callers**

Replace direct interpreter strings with imported constants in:

- `ui/ui_mainwindow.py`
- `stock/kiwoom_manager.py`

**Step 4: Keep current STOM entry argument behavior**

In `stom.py`, preserve:

- `stock` => stock auto-run
- `coin` => coin auto-run

Do not introduce a new stock-login-only mode unless Phase 3 explicitly needs it.

**Step 5: Verify interpreter string removal**

Run:

```powershell
git grep -n "subprocess.Popen(f'python32\|subprocess.Popen(f'python \|python ./stock/kiwoom_manager.py" -- ui stock
git grep -n "PYTHON_32BIT\|PYTHON_64BIT" -- utility/setting.py ui/ui_mainwindow.py stock/kiwoom_manager.py
```

Expected:

- runtime subprocesses use constants, not hardcoded interpreter names
- constants appear in the expected files

**Step 6: Commit**

```powershell
git add utility/setting.py ui/ui_mainwindow.py stock/kiwoom_manager.py stom.py
git commit -m "refactor: centralize STOM runtime python path resolution"
```

### Task 8: Review, PR, And Merge Phase 2

**Files:**
- No code changes unless review requests updates

**Step 1: Verify branch diff**

Run:

```powershell
git status --short --branch
git diff --stat main...HEAD
```

Expected: only Phase 2 files changed.

**Step 2: Push branch**

Run:

```powershell
git push -u origin feature/stom-runtime-python-paths
```

Expected: remote tracking branch created.

**Step 3: Open PR**

Run:

```powershell
gh pr create --base main --head feature/stom-runtime-python-paths --title "refactor: centralize STOM runtime python path resolution" --body "Phase 2 of STOM virtual environment migration. This PR centralizes 32-bit and 64-bit interpreter resolution for launchers and runtime subprocesses."
```

Expected: PR URL returned.

**Step 4: Wait for review and merge**

After approvals, merge the PR using the standard project flow.

**Step 5: Sync local `main`**

Run:

```powershell
git checkout main
git pull --ff-only origin main
```

Expected: local `main` includes the merged Phase 2 changes.

### Task 9: Phase 3 Branch Creation

**Files:**
- No code changes

**Step 1: Create the branch**

Run:

```powershell
git checkout -b feature/stom-venv-setup
```

Expected: HEAD moves to `feature/stom-venv-setup`.

**Step 2: Verify branch base**

Run:

```powershell
git status --short --branch
git merge-base HEAD main
git rev-parse main
```

Expected: branch is based on merged Phase 2 `main`.

**Step 3: Commit**

No commit required for this task.

### Task 10: Implement Phase 3 - Dual Venv Setup And Launchers

**Files:**
- Create: `C:/System_Trading/STOM/STOM/requirements_32bit.txt`
- Create: `C:/System_Trading/STOM/STOM/requirements_64bit.txt`
- Create: `C:/System_Trading/STOM/STOM/setup_stom.bat`
- Modify: `C:/System_Trading/STOM/STOM/stom.bat`
- Modify: `C:/System_Trading/STOM/STOM/stom_stock.bat`
- Modify: `C:/System_Trading/STOM/STOM/stom_coin.bat`
- Review only: `C:/System_Trading/STOM/STOM_MAESTRO/requirements_32bit.txt`
- Review only: `C:/System_Trading/STOM/STOM_MAESTRO/requirements_64bit.txt`
- Review only: `C:/System_Trading/STOM/STOM_MAESTRO/setup_stom.bat`

**Step 1: Define the package split**

Document exact package ownership:

- 32-bit environment: Kiwoom/OpenAPI dependencies
- 64-bit environment: main UI, analytics, coin, optimization dependencies

**Step 2: Create requirements files**

Base them on STOM's current installs and MAESTRO's proven split.

Required checks:

- `numpy==1.26.4` remains pinned
- 32-bit TA-Lib wheel stays separate from requirements
- 64-bit TA-Lib wheel stays separate from requirements

**Step 3: Create `setup_stom.bat`**

The script must:

- verify system Python paths
- create `venv_64bit` and `venv_32bit`
- upgrade pip and wheel
- install requirements
- install TA-Lib wheels
- run import-based validation
- fail fast on each critical error

**Step 4: Convert launchers to venv-aware mode**

`stom.bat`, `stom_stock.bat`, and `stom_coin.bat` must:

- verify required venv executables exist
- instruct the user to run `setup_stom.bat` if missing
- run `database_check.py` with the 64-bit venv
- run `stom.py` with the 64-bit venv
- preserve current `stock` and `coin` arguments

**Step 5: Verify file presence and key strings**

Run:

```powershell
Get-ChildItem requirements_32bit.txt,requirements_64bit.txt,setup_stom.bat
Select-String -Path setup_stom.bat -Pattern "venv_32bit","venv_64bit","TA_Lib","PYTHON32_CMD","PYTHON64_CMD"
Select-String -Path stom.bat,stom_stock.bat,stom_coin.bat -Pattern "venv_32bit","venv_64bit","setup_stom.bat","database_check.py","stom.py"
```

Expected:

- all three new files exist
- setup script references both venvs and TA-Lib wheels
- launchers reference venv executables and setup instructions

**Step 6: Commit**

```powershell
git add requirements_32bit.txt requirements_64bit.txt setup_stom.bat stom.bat stom_stock.bat stom_coin.bat
git commit -m "feat: add STOM dual virtualenv setup and launchers"
```

### Task 11: Review, PR, And Merge Phase 3

**Files:**
- No code changes unless review requests updates

**Step 1: Verify branch diff**

Run:

```powershell
git status --short --branch
git diff --stat main...HEAD
```

Expected: only Phase 3 files changed.

**Step 2: Push branch**

Run:

```powershell
git push -u origin feature/stom-venv-setup
```

Expected: remote tracking branch created.

**Step 3: Open PR**

Run:

```powershell
gh pr create --base main --head feature/stom-venv-setup --title "feat: add STOM dual virtualenv setup and launchers" --body "Phase 3 of STOM virtual environment migration. This PR adds dual 32-bit and 64-bit virtual environment setup, package installation, and venv-aware launchers."
```

Expected: PR URL returned.

**Step 4: Wait for review and merge**

After approvals, merge the PR using the standard project flow.

**Step 5: Sync local `main`**

Run:

```powershell
git checkout main
git pull --ff-only origin main
```

Expected: local `main` includes the merged Phase 3 changes.

### Task 12: Final `docs` Branch Move

**Files:**
- No code changes unless documentation reconciliation is required

**Step 1: Inspect branch positions**

Run:

```powershell
git branch --contains backup/docs-20260311
git log --oneline --decorate --graph --all --simplify-by-decoration
```

Expected: preserved backup branch still exists.

**Step 2: Decide the move strategy**

If `docs` should exactly match final `main`:

```powershell
git checkout docs
git reset --hard main
git push --force-with-lease origin docs
```

If `docs` should retain its unique doc commit first, do not use the reset flow. Instead review whether `docs` content should be rebased or merged manually.

**Step 3: Verify final branch state**

Run:

```powershell
git checkout docs
git status --short --branch
git log --oneline -n 5
```

Expected: `docs` points where intended and working tree is clean.

**Step 4: Commit**

No commit required if branch pointer move only. If doc reconciliation adds content, commit with a docs-specific message.

## Verification Checklist

Before declaring the migration complete, verify:

- Phase 1, Phase 2, and Phase 3 were merged to `main` in order
- `python64` no longer appears in supported runtime files
- `utility/setting.py` owns runtime interpreter resolution
- `setup_stom.bat` exists and creates both venvs
- `stom.bat`, `stom_stock.bat`, and `stom_coin.bat` are venv-aware
- `backup/docs-20260311` still exists before moving `docs`

## Rollback Notes

- If Phase 1 causes launcher regressions, revert only `feature/stom-python-exe-rename`
- If Phase 2 causes runtime subprocess issues, revert only `feature/stom-runtime-python-paths`
- If Phase 3 causes setup failures, revert only `feature/stom-venv-setup`
- Do not delete `backup/docs-20260311` until final validation on the merged `main` is complete

## Development Guidance

- Treat each phase as an isolated, reviewable change set
- Keep Phase 1 strictly to rename-contract work; do not mix venv logic into it
- Keep Phase 2 strictly to path resolution and runtime indirection; do not add setup automation yet
- Keep Phase 3 strictly to venv creation, requirements, and launcher verification
- If a reviewer asks for cross-phase changes, prefer landing them in the smallest correct phase or explicitly defer to the next phase
- Re-run `git status --short --branch` before any branch switch, PR creation, or merge sync

