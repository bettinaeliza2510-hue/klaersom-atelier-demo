# KlærSøm v4 experimental dynamic drafting
This revision is rebuilt from the available v2 archive; v3 archive was unavailable. It restores lazy exports, shelf-based fabric estimation and tiled printing, with a new direct Gemini geometry mode. Install Python 3.11/3.12, extract and open the klarsom folder in VS Code PowerShell.

    python -m pip install -r requirements.txt pytest
    $env:GEMINI_API_KEY="YOUR_PRIVATE_KEY"
    python app.py

Open http://127.0.0.1:5000. Select Gemini dynamic image-to-pattern, upload a dress image, consent to sending image AND measurements to Google, edit all body measurements, and submit. Optional design edits let you request changes. Manual mode stays offline. Gemini produces new polygons, variable piece counts and proposed construction notes, not just template choices. Invalid polygons are rejected instead of silently reverting to the old dress. Model can be changed with `$env:GEMINI_MODEL="MODEL_ID"`; default gemini-2.5-flash. Free quota depends on model/account; current pricing not verified. Never expose keys.

AI-generated drafts are experimental. Polygon geometry validation does not establish fit, seam compatibility, darts, internal markings or accurate reconstruction of unseen garment details. Curves are sampled polylines. Use preview and professional pattern review, verify 5 cm PDF calibration square and sew a toile. No public deployment: local only; recent designs stored in memory. The marker uses fixed 150 cm fabric and 120 gsm, conservative shelf packing and an unverified carbon factor. No measured waste saving.

Tests: `python -m pytest -q`. Engine and mock geometry tests run in build environment; Flask and live Gemini unavailable there. No claims of live image validation. Older README describes original manual workflow only. No API credentials included.
