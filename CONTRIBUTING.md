# Contributing

This repo welcomes code contributions from humans and LLMs. To keep quality high and avoid regressions, follow this read-before-edit protocol and quality gates.

## Read-before-edit checklist (order matters)
1. README.md — overview, run and support matrix
2. .copilot_wiki.md — setup/runbook/troubleshooting and conventions
3. docs/PROJECT_VISION.md — original scope and goals
4. SETUP_GUIDE.md, env_example.txt — environment, secrets, credentials
5. requirements.txt, setup.py — dependencies and packaging
6. config/default_config.py — config flags
7. Entrypoints: src/main.py, dashboards/main_dashboard.py
8. Database: src/database/models.py, src/database/database_manager.py
9. Analysis: src/analysis/ranking_engine.py
10. Data input: src/data_acquisition/market_data.py, src/data_acquisition/news_sentiment.py
11. Trading: src/trading/alpaca_client.py, src/trading/risk_manager.py
12. Tests: tests/test_integration.py

## Coding conventions
- Minimal diffs; preserve formatting where unchanged.
- Keep DB read-paths returning plain dicts; avoid ORM detachment.
- Safe datetime coercion; convert Decimal→float for UI/JSON.
- Guard for missing credentials; keep live trading disabled by default.
- Public API changes must be documented in README/wiki and tests updated.

## Quality gates (must pass before PR/commit)
- Build: repo imports, no syntax errors.
- Deps: `pip install -r requirements.txt` succeeds in a fresh venv.
- Tests: run test suite; add/adjust tests for changed behavior.
- Smoke: run `python src/analysis/ranking_engine.py` and `python -m streamlit run dashboards/main_dashboard.py` from venv without crashes.
- Docs: update README.md and .copilot_wiki.md for any user-facing changes.

## Git hooks
This repo uses a local pre-commit hook to ensure docs are updated when public code changes:
- Hook path: `.githooks/pre-commit` (repo config sets `core.hooksPath` to `.githooks`)
- If you change public files (e.g., `src/**`, `dashboards/main_dashboard.py`, `config/default_config.py`), you must stage changes to `README.md`, `.copilot_wiki.md`, `CONTRIBUTING.md`, or `docs/PROJECT_VISION.md`.
- Bypass (not recommended): `ALLOW_NO_DOCS=1 git commit -m "..."` or `git commit --no-verify`.

## Commit hygiene
- Descriptive messages.
- Scope small and focused.
- No secrets or large data files; respect .gitignore.

## Getting help
Open an issue with logs, steps to reproduce, and environment details.
