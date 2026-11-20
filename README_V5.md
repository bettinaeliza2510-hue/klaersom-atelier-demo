# KlærSøm Atelier 5.0
Windows: extract, open klarsom in VS Code PowerShell, run:

    python -m pip install -r requirements.txt pytest
    $env:GEMINI_API_KEY="YOUR_KEY"
    python app.py

Open http://127.0.0.1:5000. Click Check connection / load models, choose Automatic or a listed Flash candidate, upload image, select AI mode, consent and submit measurements. Listing is not proof of generation access. No key is stored by the app. 429 stops immediately; check quota. 503/404 may switch to one other discovered candidate; transient server failures retry at most twice per candidate. Requests may incur charges. Image and design edits are sent to Google, not body measurements in v5. Consent must be renewed and image reselected after errors. Manual mode remains the v4 offline engine.

AI uses a compact schema for garment analysis, then local geometry. Supported options: square/round/V neck, no/flat/notched collar, front buttons/back zip, sleeveless/short/puff/long sleeves, optional cuffs/sash, straight/flared/gathered skirt. Unsupported features are rejected. No arbitrary pattern generation, real lapel drafting, darts, seam matching or fit validation. Collar, facing and cuffs are rough prototype blocks only. Make a toile and seek tailor review. No automatic geometric repair: invalid geometry is rejected. The connection test only lists models. Candidate filtering is heuristic, not verified image capability. Local use only.

Tests: python -m pytest -q. In build environment 20 engine/geometry/module tests passed, including simulated shirt dress; Flask unavailable so full integration and live API not tested. Existing export and fabric estimates inherited from v4, not newly benchmarked.
