
# hatch-guide.md

## purpose (what hatch is for)
- build backend + env manager for python projects (pep 517/518)
- makes your project *packageable* (sdist/wheel), installable, and gives you cli entry points
- gives reproducible envs, versioning, and simple build/publish flow

---

## mental model
- **assume** you want repeatable builds + scripts -> **then** use a build backend (hatchling) + `[project]` metadata
- **if** you need commands run in clean envs -> **then** define `envs` and run with `hatch run`
- **since** `uv` is your installer/runner -> **then** use hatch only as the build backend + project orchestrator; call hatch via `uvx hatch`

---

## install (pick one)
- with uv (recommended for you): `uvx hatch --version`
- with pipx: `pipx install hatch`

> `uvx` runs hatch without polluting your global site-packages.

---

## minimal `pyproject.toml`
```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "trading-app"              # must be unique if publishing
version = "0.1.0"
description = "trading telemetry mvp"
readme = "README.md"
requires-python = ">=3.11"
authors = [{ name = "you" }]
dependencies = [
  # "pandas>=2.2",
]

# cli entry points installed on `pip install .` and runnable via `hatch run` too
[project.scripts]
trading-app = "trading_app.__main__:main"
```

> convention: use `src/` layout. module name should match import path above (`src/trading_app/`).

---

## repo layout (src-layout)
```
trading-app/
├─ pyproject.toml
├─ README.md
├─ src/
│  └─ trading_app/
│     ├─ __init__.py
│     └─ __main__.py   # has `def main(): ...`
└─ tests/
```

example `src/trading_app/__main__.py`:
```python
def main():
    print("trading-app cli ok")
```

---

## envs & running
- ephemeral run: `uvx hatch run trading-app` (runs your `[project.scripts]` entry)
- dev shell: `uvx hatch shell`
- run module/tests inside hatch envs:
  - `uvx hatch run python -m trading_app`
  - `uvx hatch run pytest -q`

optional: predefined envs in `pyproject.toml`:
```toml
[tool.hatch.envs.default]
dependencies = ["pytest"]
```

then: `uvx hatch run -e default pytest -q`

---

## versioning
basic (manual): keep `[project].version` in `pyproject.toml`.
automated:
```toml
[tool.hatch.version]
path = "src/trading_app/__init__.py"
```
then: `uvx hatch version minor` (or `patch`, `major`) updates that file and pyproject coherently.

---

## build & publish
- build artifacts: `uvx hatch build`  → `dist/*.whl`, `dist/*.tar.gz`
- test install: `uv pip install -e .` (editable) or `uv pip install dist/*.whl`
- publish (if desired): `uvx hatch publish` (needs PyPI creds configured)

---

## using with `uv`
- keep using `uv lock` / `uv sync` for dependency resolution
- add this so `uv` knows it’s a real package even before publishing:
```toml
[tool.uv]
package = true
```

- after that, `uv run trading-app` works because entry points are installed in the project venv

workflow summary:
1) write code under `src/`
2) define `[project]` + `[project.scripts]`
3) set hatchling as backend (`[build-system]`)
4) `uv lock && uv sync`
5) `uv run trading-app` (or `uvx hatch run trading-app`)
6) `uvx hatch build` when you want artifacts

---

## testing matrix (optional)
```toml
[tool.hatch.envs.test]
dependencies = ["pytest"]
[tool.hatch.envs.test.matrix]
python = ["3.11", "3.12"]

# run all:
# uvx -p 3.12 hatch run -e test pytest -q
```
(you can repeat for multiple interpreters if installed.)

---

## migration checklist (from current state)
- [ ] move code to `src/trading_app/`
- [ ] add `[build-system]` with `hatchling`
- [ ] fill `[project]` metadata; add `[project.scripts]`
- [ ] add `[tool.uv] package = true`
- [ ] `uv lock && uv sync`
- [ ] `uv run trading-app` → expect no more “project isn’t packaged” warning

---

## troubleshooting
- **warning: skipping installation of entry points** → set `[tool.uv].package = true` *and/or* define a `build-system` (hatchling).
- **entry point not found** → module path in `[project.scripts]` must resolve (importable from `src/`).
- **editable install problems** → ensure src-layout + `__init__.py` present.
- **multiple tools conflict** → avoid mixing poetry/setuptools metadata with hatchling in the same project.

---

## tl;dr
- hatch = build backend + env runner; pair it with `uv` for speed.
- define `[project]` + `[project.scripts]`, set hatchling in `[build-system]`, keep `src/` layout.
- you’ll get clean cli, reproducible envs, easy builds, and no more `uv` warnings.
