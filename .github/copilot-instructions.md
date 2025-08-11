# Algorithmic Investment Framework

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test the Repository
- **Environment Setup:**
  - `python -m venv venv` -- creates virtual environment (takes ~3 seconds)
  - `source venv/bin/activate` -- activate virtual environment (Linux/macOS)
  - `venv\Scripts\activate` -- activate virtual environment (Windows)
  - `python -m pip install --upgrade pip` -- upgrade pip (takes ~2-3 seconds)
  - `pip install -r requirements.txt` -- **CRITICAL: Can take 15-45 minutes. NEVER CANCEL. Set timeout to 60+ minutes.**
    - **KNOWN ISSUE**: Network timeouts are frequent with PyPI. If install fails:
      - Retry with: `pip install --timeout 120 --retries 5 -r requirements.txt`
      - Or install in batches: `pip install pandas numpy yfinance requests beautifulsoup4 nltk vaderSentiment streamlit plotly`
      - Then: `pip install -r requirements.txt` for remaining packages
    - **Alternative**: Some environments may need `pip install --no-cache-dir -r requirements.txt`

### Quick Syntax and Structure Validation (No Dependencies Required)
- `find src/ -name "*.py" -exec python -m py_compile {} \;` -- validates Python syntax in all source files (~5 seconds)
- `python -c "import sys; sys.path.append('src'); print('✅ Python path setup correct')"` -- tests import path setup
- `ls -la src/ tests/ dashboards/` -- verify key directories exist
- `head -10 requirements.txt` -- check dependency list format

### Pre-Installation Validation 
- `python --version` -- must be 3.8+ (3.9+ recommended)
- `python -m venv --help` -- verify venv module available
- `cp env_example.txt .env && ls -la .env` -- test environment setup

### Download NLTK Data (Required After Package Installation)
- `python -c "import nltk; nltk.download('vader_lexicon')"` -- downloads sentiment analysis data (~30 seconds)
- **Note**: This requires working internet connection and successful package installation

### Common Packages in Requirements.txt
```
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing  
yfinance>=0.2.18       # Yahoo Finance API
streamlit>=1.28.0      # Web dashboard
plotly>=5.15.0         # Interactive charts
requests>=2.31.0       # HTTP requests
beautifulsoup4>=4.12.0 # Web scraping
nltk>=3.8.1            # Natural language processing
vaderSentiment>=3.3.2  # Sentiment analysis
sqlalchemy>=2.0.0      # Database ORM
alpaca-py>=0.8.0       # Trading API
transformers>=4.30.0   # Advanced NLP models
torch>=2.0.0           # Machine learning
scikit-learn>=1.3.0    # Classical ML
```

### Environment Configuration
- `cp env_example.txt .env` -- copy environment template
- Edit `.env` file with your actual API keys (optional for basic functionality)

### Run the Core Analysis System
- **ALWAYS** run the bootstrapping steps first
- `python src/main.py` -- runs complete stock analysis (takes 2-5 minutes depending on network)
- `python src/main.py test` -- runs component tests (takes 30-60 seconds)

### Run the Interactive Dashboard
- **ALWAYS** run from activated virtual environment
- `python -m streamlit run dashboards/main_dashboard.py` -- launches web dashboard on port 8501
- **CRITICAL**: Use `python -m streamlit`, NOT `streamlit` to avoid import errors
- Access dashboard at `http://localhost:8501`

### Run Tests
- `python tests/test_integration.py` -- runs integration test suite (takes 2-3 minutes. NEVER CANCEL. Set timeout to 10+ minutes)

## Validation

### ALWAYS Validate Functionality After Changes
- **Mandatory validation steps:**
  1. Run `python src/main.py test` to verify core components
  2. Launch dashboard: `python -m streamlit run dashboards/main_dashboard.py` 
  3. Test at least one complete workflow in the dashboard (select stocks, run analysis, view results)
  4. **NEVER skip validation** - it takes 5-10 minutes but prevents major issues

### Manual Testing Scenarios
- **Stock Analysis Workflow**: 
  1. Open dashboard with `python -m streamlit run dashboards/main_dashboard.py`
  2. Enter stock symbols (e.g., AAPL, MSFT, GOOGL) in the input field
  3. Click "Run Analysis" or similar button
  4. **Verify results display**: Check for composite scores, technical scores, sentiment scores
  5. **Check rankings**: Verify stocks are ranked by composite score (highest first)
  6. **Check CSV output**: Look for new file in `data/` folder with timestamp format `rankings_YYYYMMDD_HHMMSS.csv`
  7. **Validate CSV content**: Should contain columns: rank, ticker, composite_score, technical_score, sentiment_score, price, percent_change, volume, headline_count, positive_ratio, negative_ratio

- **Command Line Analysis Workflow**:
  1. Run `python src/main.py` 
  2. **Verify output**: Should show ranking table with top 10 picks
  3. **Check file generation**: New CSV should appear in `data/` directory
  4. **Sample expected output format**:
     ```
     rank,ticker,composite_score,technical_score,sentiment_score,price,percent_change,volume,headline_count,positive_ratio,negative_ratio,sentiment_std
     1,AAPL,85.24,100.0,63.11,229.35,4.24,113696100,20,0.45,0.05,0.29
     ```

- **Component Testing Workflow**:
  1. Run `python src/main.py test`
  2. **Verify**: Should show "✅ Market data test passed" and "✅ Sentiment analysis test passed"
  3. **No errors**: Should complete without ModuleNotFoundError or network timeouts

## Common Tasks

### Dependency Management
- **Install new packages**: `pip install package_name` (from activated venv)
- **Update requirements**: `pip freeze > requirements.txt`
- **Clean install**: Delete `venv/` folder and re-run bootstrap steps

### Development Workflow
- **Before making changes**: Always run `python src/main.py test` to verify baseline
- **After making changes**: Run validation steps (test + dashboard + manual scenario)
- **Debug issues**: Check `logs/framework.log` for detailed error information

### Performance Expectations
- **Virtual environment creation**: 3 seconds
- **Pip upgrade**: 2-3 seconds  
- **Full dependency install**: 15-45 minutes (NEVER CANCEL)
- **NLTK data download**: 30 seconds
- **Component test**: 30-60 seconds
- **Full analysis**: 2-5 minutes (network dependent)
- **Integration tests**: 2-3 minutes (NEVER CANCEL - set 10+ minute timeout)
- **Dashboard startup**: 10-30 seconds

## Important Warnings

### NEVER CANCEL Operations
- **`pip install -r requirements.txt`** -- Can take up to 45 minutes, especially on first install
- **Integration tests** -- Can take 3+ minutes to fetch real market data
- **Any command with network operations** -- Market data and news fetching can be slow

### Network Dependencies
- **Market Data**: Uses Yahoo Finance (no API key required) and optional Alpha Vantage
- **News Data**: Fetches from multiple sources for sentiment analysis
- **Installation**: PyPI package downloads can timeout - this is normal, retry with longer timeouts

## Repository Structure

### Key Entry Points
- `src/main.py` -- Core analysis engine and CLI interface
- `dashboards/main_dashboard.py` -- Streamlit web interface  
- `tests/test_integration.py` -- Comprehensive test suite
- `quick_start.py` -- Interactive setup script

### Critical Directories
- `src/analysis/` -- Ranking algorithms and scoring logic
- `src/data_acquisition/` -- Market data and news fetching
- `src/database/` -- Data persistence and models
- `src/trading/` -- Alpaca integration and risk management
- `config/` -- Configuration files
- `data/` -- Local data storage (SQLite DB, CSV outputs)
- `logs/` -- Application logs (`framework.log`)

### Important Files
- `requirements.txt` -- All Python dependencies
- `env_example.txt` -- Environment variable template
- `.env` -- Your actual API keys (create from template)
- `README.md` -- Project overview and quick start
- `SETUP_GUIDE.md` -- Detailed setup instructions

## Troubleshooting

### Common Issues
- **"Module not found" errors**: Ensure virtual environment is activated
- **Streamlit import errors**: Use `python -m streamlit` instead of `streamlit`
- **Network timeouts during install**: 
  - Retry with `pip install --timeout 120 --retries 5 -r requirements.txt`
  - Try `pip install --no-cache-dir -r requirements.txt`
  - Install core packages first: `pip install pandas numpy requests streamlit`
- **Empty analysis results**: Check internet connection and API rate limits
- **Dashboard won't start**: Check if port 8501 is available, try `--server.port 8502`
- **Permission errors**: Ensure you have write access to the directory

### Quick Diagnostics
- `python --version` -- should be 3.8+
- `which python` -- should point to your venv when activated (`...venv/bin/python`)
- `pip list` -- check installed packages
- `python -c "import requests, pandas, numpy"` -- test core dependencies
- `ls -la logs/` -- check log directory (should contain `framework.log`)
- `tail -20 logs/framework.log` -- view recent log entries
- `python -c "import sys; print(sys.path)"` -- verify Python path includes project

### Log Files and Debugging
- **Main log file**: `logs/framework.log` -- contains all application logging
- **Check for errors**: `grep -i error logs/framework.log`
- **Check last run**: `tail -50 logs/framework.log`
- **Clear logs**: `> logs/framework.log` -- empties the log file for fresh debugging

## API Keys and Configuration

### Required for Basic Functionality
- **None** -- Framework works with Yahoo Finance without API keys

### Optional Enhancements  
- **Alpha Vantage** -- Enhanced market data (sign up at alphavantage.co)
- **Alpaca** -- Paper/live trading integration (sign up at alpaca.markets)

### Always Start with Paper Trading
- Never use live trading keys initially
- Test with paper trading account first
- Verify all functionality before considering live trading

## CI/CD and Development Workflow

### Git Hooks Setup (Recommended)
- `git config core.hooksPath .githooks` -- enables pre-commit documentation checks
- **Pre-commit hook requirement**: When changing public code (src/analysis/, src/data_acquisition/, src/database/, src/trading/, dashboards/main_dashboard.py, src/main.py, config/default_config.py), you must also update documentation files (README.md, .copilot_wiki.md, CONTRIBUTING.md, or docs/PROJECT_VISION.md)
- **Override hook**: `export ALLOW_NO_DOCS=1` or `git commit --no-verify` to bypass

### GitHub Workflows
- **docs-policy.yml**: Enforces documentation updates when public APIs change
- **No build workflow**: Project relies on local Python environment setup
- **Manual testing required**: No automated test runs in CI

### Development Best Practices
- **Always update docs**: When changing public APIs or behavior
- **Test locally first**: Run validation scenarios before committing  
- **Use meaningful commit messages**: Especially for public API changes
- **Monitor logs**: Check `logs/framework.log` for issues during development

## Safety and Risk Management

### Development Safety
- **Always test changes thoroughly** -- Run validation scenarios
- **Check logs** -- Monitor `logs/framework.log` for errors
- **Start small** -- Test with 2-3 stocks before large analyses

### Trading Safety
- **Paper trading only initially** -- Never use live trading without extensive testing
- **Risk limits built-in** -- Framework limits position sizes and risk exposure
- **Manual oversight required** -- Never run automated trading without supervision

## Complete Setup and Validation Example

### Full First-Time Setup (Copy-Paste Workflow)
```bash
# 1. Environment setup (3 seconds)
python -m venv venv
source venv/bin/activate  # Linux/macOS (or venv\Scripts\activate on Windows)

# 2. Upgrade pip (2-3 seconds)  
python -m pip install --upgrade pip

# 3. Install dependencies (15-45 minutes, NEVER CANCEL)
pip install -r requirements.txt
# If network issues: pip install --timeout 120 --retries 5 -r requirements.txt

# 4. Download NLTK data (30 seconds)
python -c "import nltk; nltk.download('vader_lexicon')"

# 5. Setup environment file
cp env_example.txt .env
# Edit .env file with your API keys (optional for basic functionality)

# 6. Enable git hooks (recommended)
git config core.hooksPath .githooks

# 7. Validate installation
python src/main.py test

# 8. Run full analysis (2-5 minutes)
python src/main.py

# 9. Launch dashboard
python -m streamlit run dashboards/main_dashboard.py
# Dashboard available at http://localhost:8501
```

### Quick Development Workflow
```bash
# Start of work session
source venv/bin/activate

# Make your code changes...

# Validate changes
python src/main.py test                              # Component test
python -m streamlit run dashboards/main_dashboard.py  # Manual validation

# Before committing (if changing public APIs)
# Update README.md or .copilot_wiki.md with your changes

# Commit
git add .
git commit -m "Your meaningful commit message"
```

---

**Last Updated**: Generated from repository analysis on August 11, 2025