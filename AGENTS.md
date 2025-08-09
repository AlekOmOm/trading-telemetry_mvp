# Repository Guidelines

## Project Structure & Module Organization
- `docs/`: Product and planning docs (see `docs/MVP.PRD.md`).
- `src/`: Application code (create per service/module as the codebase grows).
- `tests/`: Automated tests mirroring `src/` structure.
- `config/`: Local config, environment templates, and sample files (e.g., `.env.example`).
- Keep modules small and cohesive; prefer `package/` (folder) over single large files.

## Build, Test, and Development Commands
- No build tooling is committed yet. Prefer adding a `Makefile` with common targets:
  - `make setup`: Install deps for the chosen stack(s).
  - `make run`: Start the app locally (document entrypoint in `README.md`).
  - `make lint` / `make fmt`: Lint/format code.
  - `make test`: Run the full test suite.
- Example (Python): `pip install -r requirements.txt && pytest -q`.
- Example (Node): `npm ci && npm test`.

## Coding Style & Naming Conventions
- Indentation: Python 4 spaces; JS/TS 2 spaces. Wrap at ~100 chars.
- Names: `snake_case` for files in Python; `kebab-case` for JS packages; `PascalCase` for types/classes.
- Formatting/Linting (recommend): Python `black`, `ruff`; JS/TS `prettier`, `eslint`.
- Commit formatters/lint hooks are encouraged via `pre-commit`.

## Testing Guidelines
- Place tests in `tests/` with one-to-one module mapping.
- Names: Python `test_*.py`; JS/TS `*.spec.ts`/`*.test.ts`.
- Aim for meaningful coverage on core logic and edge cases; add fixtures for external I/O.
- Fast unit tests > slow end-to-end; mark slow tests with a tag/skip.

## Commit & Pull Request Guidelines
- History currently lacks a convention; adopt Conventional Commits (e.g., `feat: add trade ingestion`).
- PRs: concise description, linked issue, clear screenshots/logs for UX or DX changes.
- Keep PRs small and focused; include `How to test` steps and any config changes.

## Security & Configuration Tips
- Never commit secrets. Use `.env` locally and `*.example` templates in `config/`.
- Document required env vars in `README.md`; prefer typed config loaders where possible.
