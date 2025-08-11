# 📒 Product Backlog

Single source of truth for upcoming work. Use the template below for each user story.

## Template

Story: As a [user type], I want to [perform some action] so that I can [achieve some goal].

- [ ] Task `TASK-001`: First actionable step.
- [ ] Task `TASK-002`: Second actionable step.

---

## Backlog

<!-- Add new stories below this line -->

Story: As a user, I want to run a core analysis to get ranked investment ideas so that I can review top picks quickly.

- [ ] Task `TASK-001`: Ensure `python src/main.py` runs end-to-end and saves CSV to `data/`.
- [ ] Task `TASK-002`: Print a concise top-10 summary table in the console.

---

Story: As a user, I want to view rankings and details in a dashboard so that I can explore interactively.

- [ ] Task `TASK-003`: Verify `python -m streamlit run dashboards/main_dashboard.py` launches from repo root.
- [ ] Task `TASK-004`: Show ranked table + simple price chart for selected ticker.

---

Story: As an analyst, I want reliable price data with fallback so that transient API issues don’t block analysis.

- [ ] Task `TASK-005`: Use Yahoo Finance as primary, Alpha Vantage as optional fallback (configurable).
- [ ] Task `TASK-006`: Add provider selection arg/env and log which provider is used.

---

Story: As an analyst, I want recent news sentiment per ticker so that rankings reflect market mood.

- [ ] Task `TASK-007`: Scrape FinViz headlines with respectful rate limits and error handling.
- [ ] Task `TASK-008`: VADER-based sentiment with finance-keyword boost and headline counts.

---

Story: As a quant, I want a composite scoring system so that I can balance technicals and sentiment.

- [ ] Task `TASK-009`: Normalize technical and sentiment scores to 0–100 (min-max or z-score).
- [ ] Task `TASK-010`: Make weights configurable; validate they sum to 1.0.

---

Story: As a user, I want “top picks” with simple recommendations so that I can act on the results faster.

- [ ] Task `TASK-011`: Implement `get_top_picks(...)` with min-headlines filter and labels (Strong Buy/Buy/etc.).
- [ ] Task `TASK-012`: Print a concise “Top Picks” section after analysis.

---

Story: As a developer, I want rankings saved to the database so that results are queryable later.

- [ ] Task `TASK-013`: Persist ranking results via SQLAlchemy (`save_ranking_results`).
- [ ] Task `TASK-014`: Read DB URL from env; default to SQLite in `data/`.

---

Story: As a trader, I want paper trading via Alpaca so that I can test execution safely.

- [ ] Task `TASK-015`: Create Alpaca client wrapper using paper trading keys from `.env`.
- [ ] Task `TASK-016`: Execute small test orders from top picks with dry-run option and logging.

---

Story: As a risk manager, I want guardrails on trades so that the system avoids outsized risk.

- [ ] Task `TASK-017`: Position sizing rules (e.g., max 2% risk per position, 10% allocation cap).
- [ ] Task `TASK-018`: Default stop-loss/take-profit parameters; daily trade limits.

---

Story: As an operator, I want robust logging so that I can troubleshoot quickly.

- [ ] Task `TASK-019`: Log to `logs/framework.log` + console with timestamps and module names.
- [ ] Task `TASK-020`: Add key checkpoints (start/end analysis, provider choices, errors).

---

Story: As an operator, I want clean environment configuration so that setup is repeatable.

- [ ] Task `TASK-021`: Support `.env` via python-dotenv; provide `env_example.txt`.
- [ ] Task `TASK-022`: Docs: clarify which keys are optional vs required.

---

Story: As a maintainer, I want a basic integration test so that regressions are caught.

- [ ] Task `TASK-023`: Ensure `tests/test_integration.py` covers a smoke run of ranking with 2–3 tickers.
- [ ] Task `TASK-024`: Make test resilient to network hiccups (skip/xfail when providers unavailable).

---

Story: As an analyst, I want optional FinBERT sentiment so that I can compare with VADER.

- [ ] Task `TASK-025`: Add FinBERT pipeline behind a config flag with graceful dependency checks.
- [ ] Task `TASK-026`: Side-by-side evaluation on a sample to compare scores and runtime.

---

Story: As a data engineer, I want PostgreSQL support for production so that data scales beyond SQLite.

- [ ] Task `TASK-027`: Accept `DATABASE_URL=postgresql+psycopg2://...` and verify migrations/indexes.
- [ ] Task `TASK-028`: Add short setup notes for Postgres in SETUP_GUIDE.md.

---

Story: As a data engineer, I want optional InfluxDB time-series storage so that price data is efficient at scale.

- [ ] Task `TASK-029`: Add write path for OHLCV to InfluxDB (config gated).
- [ ] Task `TASK-030`: Minimal read/query helper and docs.

---

Story: As a quant, I want a simple backtesting harness so that I can evaluate strategy ideas.

- [ ] Task `TASK-031`: Add a lightweight backtest runner over historical daily data.
- [ ] Task `TASK-032`: Report CAGR, Sharpe, and max drawdown.

---

Story: As a user, I want alerting on high-scoring assets so that I don’t miss opportunities.

- [ ] Task `TASK-033`: CLI/email alert for assets crossing a score threshold.
- [ ] Task `TASK-034`: Add a simple scheduler example for daily runs.

---

Story: As an ML engineer, I want a baseline ML ranking model so that I can explore predictive ranking.

- [ ] Task `TASK-035`: Feature engineering scaffolding (technical + sentiment features).
- [ ] Task `TASK-036`: Baseline model (e.g., LightGBM) with offline evaluation.

---

Story: As a maintainer, I want docs to stay consistent so that users aren’t confused.

- [ ] Task `TASK-037`: Add a doc-check reminder in CONTRIBUTING and PR template (done; verify in use).
- [ ] Task `TASK-038`: Keep README/SETUP_GUIDE/wiki in sync when public behavior changes.

