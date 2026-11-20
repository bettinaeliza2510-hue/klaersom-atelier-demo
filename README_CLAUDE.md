# KlærSøm Atelier — Setup Guide

This folder is the whole app. There is no GitHub repo involved — just copy the
folder to your machine and follow the steps below. Everything runs locally
on your own computer; nothing is uploaded anywhere unless you deliberately
turn on the optional Gemini AI mode (see below).

## What this is

A small Flask web app that turns body measurements into a basic dress sewing
pattern: pick a neckline and skirt style, enter your measurements, and it
draws dot-to-dot pattern pieces you can print or export (PNG/SVG/PDF/CSV).
It's an educational prototype, not a validated patternmaking tool — see
**Honest limitations** at the bottom.

## 1. Prerequisites

- **Python 3.10 or newer** (built and tested on 3.12). Check with:
  ```
  python --version
  ```
  On Windows, if `python` isn't recognised, try `py --version` instead.
- No Node.js, no database, no Docker — just Python.
- Internet access is only needed for: installing the packages below, loading
  the Google Fonts used on the page (it falls back to system fonts if
  offline), and the optional Gemini AI mode. The core app works fully offline.

## 2. Install and run

Open a terminal **inside this folder** and run the commands for your OS.

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Or just double-click **START_WINDOWS.bat**, which installs dependencies and
starts the server for you (no virtual environment, uses your system Python).

### macOS / Linux (bash/zsh)
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser. Press `Ctrl+C` in the
terminal to stop the server.

Every time you come back to work on this in a new terminal, re-activate the
virtual environment first (`.\.venv\Scripts\Activate.ps1` or
`source .venv/bin/activate`) before running `python app.py` again.

## 3. Check it worked

- The home page should show the KlærSøm hero banner with a **Start drafting**
  button.
- Click it, click one of the **sample** buttons to fill in measurements, and
  press **Draft my dress pattern** — you should see five pattern pieces with
  downloadable PNG/SVG/PDF files.
- Run the automated test suite to double-check the install:
  ```
  python test_app.py
  python test_drafting.py
  ```
  (these two run standalone and print `PASS` for each test). For the full
  suite including the AI-mode unit tests, install `pytest` and run:
  ```
  python -m pip install pytest
  python -m pytest -q
  ```
  All 28 tests should pass.

## 4. Optional: turning on the Gemini AI mode

The default **Manual offline** drafting mode needs no API key and never
sends anything anywhere. There's a second mode, **Gemini dynamic
image-to-pattern**, which sends an uploaded reference image (and any typed
design notes — never your body measurements) to Google's Gemini API to
sketch a dress automatically. It's optional and off unless you explicitly
choose it and tick the consent box on the page.

To use it you need your own Gemini API key (free tier available) from
[Google AI Studio](https://aistudio.google.com/apikey). Then set it as an
environment variable **in the same terminal session** before starting the
app:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = "your-key-here"
python app.py
```

**macOS/Linux:**
```bash
export GEMINI_API_KEY="your-key-here"
python3 app.py
```

> Note: this app does **not** auto-load a `.env` file — setting
> `GEMINI_API_KEY` in a `.env` file alone will do nothing. You must export it
> in the shell you launch `python app.py` from, every session (or add it to
> your system/user environment variables permanently, or to your shell
> profile so it's always set).

Optional: set `GEMINI_MODEL` to pin a specific model id instead of letting
the app auto-pick one. Never share your API key or commit it anywhere.

## 5. Project layout

| File / folder | Job |
|---|---|
| `app.py` | Flask routes: pages, form handling, downloads |
| `drafting.py` | Manual-mode pattern maths and geometry (no Flask) |
| `modular.py`, `ai_drafting.py`, `gemini.py` | Gemini AI-mode: garment spec, geometry validation, API calls |
| `plotting.py` | Draws pattern pieces and exports PNG/PDF/SVG |
| `extras.py` | Fabric marker/estimate and tiled A4 PDF export |
| `config.py` | Sample sizes, input limits, drafting constants |
| `templates/landing.html` | Marketing/home page (`/`) |
| `templates/studio.html` | The design form and results page (`/studio`) |
| `static/css/atelier.css`, `static/js/atelier.js` | Styling and front-end behaviour |
| `test_*.py` | 28 automated tests across the engine, Flask app and AI mode |

### Pages and routes
- `/` — landing page (how it works + a sample pattern gallery)
- `/studio` — the measurement form; also where results appear after drafting
- `/health` — JSON health check
- `/gemini-models` — lists available Gemini models (used by the "Check
  connection" button)
- `/plot/<token>/<i>`, `/download/...`, `/reference/<token>` — generated
  images and files for a specific draft; `<token>` only exists for drafts
  made in the current server session (kept in memory, never written to disk)

## 6. Troubleshooting

- **`ModuleNotFoundError`** — you skipped `pip install -r requirements.txt`,
  or forgot to activate the virtual environment first.
- **`python`/`pip` not recognised (Windows)** — use the `py` launcher
  instead: `py -m venv .venv`, `py -m pip install -r requirements.txt`, `py app.py`.
- **Port 5000 already in use** — another program (or a previous run of this
  app) is using it. Stop it, or edit the last line of `app.py` and change
  `port=5000` to something else, e.g. `port=5050`.
- **Install fails building `shapely` or `matplotlib`** — make sure you're on
  Python 3.10+ and have upgraded pip first (`python -m pip install --upgrade pip`);
  these ship pre-built wheels for recent Python versions so a compiler
  shouldn't be needed.
- **Windows Firewall popup on first run** — click **Allow**; the app only
  listens on `127.0.0.1` (your own machine), it isn't exposed to your network.
- **Fonts look like a generic sans-serif** — you're offline or Google Fonts
  is blocked; the page still works, it just falls back to system fonts.

## Honest limitations

- Formulas are heuristics, not validated patternmaking. No darts, no fitted
  back shaping.
- Sleeve and skirt are simplified; skirt gathering is a ratio, not a full
  gathering plan.
- PDFs are previews: print scale is not verified. Use the 10 cm scale bar
  printed on each piece to check your printer's scaling.
- Gemini AI mode is experimental: it validates geometry (no self-crossing
  edges, no NaNs) but does not validate fit, seam compatibility, or sewing
  feasibility.
- Always make a toile (test garment) before cutting good fabric.
