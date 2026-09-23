# Contributing to winvda

This guide details the development workflow, quality gates, and patch submission requirements for `winvda`.

---

## 1. Development Environment Setup

`winvda` uses Python standard library `ctypes` without external runtime dependencies. Development tooling requires Python 3.10 or higher.

1. Clone the repository:
   ```powershell
   git clone https://github.com/amirf147/winvda.git
   ```
2. Create and activate a virtual environment:
   ```powershell
   py -3.10 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install development dependencies:
   ```powershell
   pip install -e .[dev]
   pip install ruff build twine
   ```

---

## 2. Pre-Flight Validation Sequence

Every change must pass the following validation sequence before submitting a pull request:

### Step 1: Run the Test Suite
Execute integration and unit tests:
```powershell
py -3.10 -m pytest -v
```

### Step 2: Code Quality and Formatting Checks
Run the Ruff linter and format checker:
```powershell
py -3.10 -m ruff check .
py -3.10 -m ruff format --check .
```
To reformat code automatically:
```powershell
py -3.10 -m ruff format .
```

### Step 3: Safety, Secret, and Path Hygiene Scan
Execute the repository hygiene audit to verify that no hardcoded user paths, machine metadata, or credential tokens are committed:
```powershell
py -3.10 scripts/check_repo_safety.py
```

### Step 4: Markdown Link Resolution
Ensure all internal and external markdown references resolve:
```powershell
py -3.10 scripts/verify_markdown_links.py
```

---

## 3. Commit Message Conventions

Commit messages must adhere to conventional commits with granular subsystem scopes.

### Format
```text
type(scope): imperative title

Body paragraph explaining why the change was needed and the architectural context.

* Bulleted list of concrete changes.
```

### Allowed Types
* `feat`: New feature or user-facing API additions.
* `fix`: Bug fix or defect resolution.
* `docs`: Documentation additions or revisions.
* `refactor`: Code restructuring without behavioral changes.
* `test`: Test suite additions or corrections.
* `ci`: Workflow or build configuration modifications.
* `chore`: Maintenance updates to tooling or dependencies.

### Scopes
Use granular scopes identifying the exact component:
* `core/engine`: Changes to `winvda/engine.py`.
* `core/pinning`: Changes to `winvda/pinning.py`.
* `core/vtables`: Changes to `winvda/_vtables.py`.
* `core/win32`: Changes to `winvda/_win32.py`.
* `cli`: Changes to `winvda/__main__.py`.
* `packaging`: Changes to `pyproject.toml` or package markers.

### Constraints
* Use lowercase imperative mood without a trailing period in the title.
* Autonomous commits and direct pushes to `master` without review are prohibited.

---

## 4. Pull Request Protocol

1. Create a focused topic branch from `master`.
2. Keep pull requests scoped to a single logical issue or enhancement.
3. Verify that all automated GitHub Actions CI jobs pass.
