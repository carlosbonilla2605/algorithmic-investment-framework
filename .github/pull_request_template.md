# Pull Request

## Summary
- What does this change do and why?
- Scope (modules/files touched):

## Checklist (required)
- [ ] I read, in order, before editing:
  - [ ] README.md
  - [ ] .copilot_wiki.md
  - [ ] docs/PROJECT_VISION.md
  - [ ] SETUP_GUIDE.md and env_example.txt
  - [ ] requirements.txt and setup.py
  - [ ] config/default_config.py
  - [ ] Entrypoints: src/main.py, dashboards/main_dashboard.py
  - [ ] DB layer: src/database/models.py, src/database/database_manager.py
  - [ ] Analysis: src/analysis/ranking_engine.py
  - [ ] Data input: src/data_acquisition/market_data.py, src/data_acquisition/news_sentiment.py
  - [ ] Trading: src/trading/alpaca_client.py, src/trading/risk_manager.py
  - [ ] tests/test_integration.py
- [ ] I kept diffs minimal and avoided reformatting unrelated code
- [ ] Public APIs preserved or changes documented
- [ ] DB read paths still return plain dicts; no ORM detachment
- [ ] Safe date coercion and Decimal→float conversions preserved
- [ ] Guards for missing credentials; live trading remains disabled by default
- [ ] Documentation updated as needed:
  - [ ] README.md and/or .copilot_wiki.md
  - [ ] CONTRIBUTING.md (if process changed)
  - [ ] docs/PROJECT_VISION.md (if scope changed)
- [ ] Tests:
  - [ ] Existing tests pass
  - [ ] Added/updated tests for behavior changes
- [ ] Smoke tests (locally):
  - [ ] python src/main.py runs without crashing
  - [ ] python -m streamlit run dashboards/main_dashboard.py launches from the active venv

## Risk/Impact
- Backward compatibility concerns:
- DB schema or data migration required:
- Operational impact (env vars, secrets, rate limits):

## Screenshots/Logs (optional)
- Include relevant UI screenshots or terminal logs

## Additional Notes
- Anything reviewers should pay attention to
