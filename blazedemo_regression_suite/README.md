# BlazeDemo Enterprise Regression Suite

A professional-grade, end-to-end automated cross-browser regression test suite for [BlazeDemo](https://blazedemo.com) built with **Python 3.10+**, **Selenium WebDriver 4**, and **Pytest**.

---

## 📁 Project Structure

```
blazedemo_regression_suite/
├── config/               # Config singleton + settings JSON
├── pages/                # Page Object Model classes (POM)
├── test_data/            # Parameterised datasets & passenger payloads
├── tests/                # Test files + conftest.py fixtures
├── utilities/            # Colorized logger (console + rotating file)
├── reports/
│   └── screenshots/      # Auto-created; failure screenshots saved here
├── pytest.ini            # Markers, timeout, logging config
└── requirements.txt      # Pinned dependencies
```

---

## 🚀 Setup

### 1. Create & Activate a Virtual Environment

```powershell
# From the blazedemo_regression_suite directory
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## ▶️ Running Tests

All commands should be run from **inside** the `blazedemo_regression_suite/` directory.

### Full headless Chrome suite (recommended for CI)

```powershell
pytest -v -s --browser=chrome --headless --html=reports/report.html --self-contained-html
```

### Full suite — non-headless (visible browser, useful for debugging)

```powershell
pytest -v -s --browser=chrome --html=reports/report.html --self-contained-html
```

### Parallel execution (4 workers)

```powershell
pytest -v -n 4 --browser=chrome --headless --html=reports/report.html --self-contained-html
```

### Firefox headless

```powershell
pytest -v -s --browser=firefox --headless --html=reports/report.html --self-contained-html
```

### Run only smoke tests

```powershell
pytest -v -s -m smoke --browser=chrome --headless --html=reports/report.html --self-contained-html
```

### Run only E2E tests

```powershell
pytest -v -s -m e2e --browser=chrome --headless --html=reports/report.html --self-contained-html
```

---

## 📊 Reports

After running, open the HTML report in any browser:

```powershell
# Windows
Start-Process reports/report.html
```

Or navigate to the file path in your browser:
```
blazedemo_regression_suite/reports/report.html
```

**Failure screenshots** are auto-captured to:
```
blazedemo_regression_suite/reports/screenshots/FAIL_<test_name>_<timestamp>.png
```

**Log file** (DEBUG level):
```
blazedemo_regression_suite/reports/test_run.log
```

---

## 🧪 Test Inventory

| File | Marker | Description |
|---|---|---|
| `test_flight_search.py` | `smoke`, `regression` | Home page load + 3-route parametrized search |
| `test_e2e_booking.py` | `e2e`, `regression` | Full Paris→Buenos Aires booking with confirmation |
| `test_negative_cases.py` | `negative`, `regression` | Empty field submission, default route, direct URL |

---

## 🌐 Browser Support

| Browser | CLI Flag | Notes |
|---|---|---|
| Chrome | `--browser=chrome` | Default; uses ChromeDriverManager |
| Firefox | `--browser=firefox` | Uses GeckoDriverManager |
| Edge | `--browser=edge` | Uses EdgeChromiumDriverManager |

---

## 🏗️ Architecture

The suite follows the **Page Object Model (POM)** pattern:

- **`BasePage`**: All wait abstractions, retry logic for stale elements, JS scroll, screenshot helper.
- **No `time.sleep()`**: All element interactions use `WebDriverWait` + `expected_conditions`.
- **Function-scoped drivers**: Each test gets a fresh browser instance for complete isolation.
- **Screenshot on failure**: `pytest_runtest_makereport` hook captures and attaches screenshots automatically.
