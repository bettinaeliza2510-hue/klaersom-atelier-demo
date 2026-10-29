# KlærSøm: Dress Pattern Atelier (demo build)

Measurements in, dot-to-dot dress pattern out. Runs fully offline.

## Run (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python test_drafting.py
python test_app.py
python app.py
```
Open http://127.0.0.1:5000

## What it does
- Five pieces: front bodice, back bodice, skirt panel, puff sleeve, waist sash.
- Curved armholes, necklines and sleeve cap (quadratic Bezier curves sampled into labelled dots).
- Seam allowance is a geometric offset. Fold edges get none; the skirt hem gets 3 cm.
- Seam and fit checks: shoulder and side seams match, ease, skirt gathering ratio, sleeve cap vs armhole.
- Options that change the output: neckline, skirt style, skirt fullness, sleeve puff.
- Downloads: PNG, SVG, PDF per piece; all pieces in one PDF; coordinates as CSV.
- Reference image is shown only. It is NOT analysed. It stays in memory, never on disk.

## Files
| File | Job |
|---|---|
| `drafting.py` | All pattern maths and geometry (no Flask). Explain this in the viva. |
| `plotting.py` | Draws pieces, exports PNG / PDF / SVG |
| `app.py` | Flask routes, input validation, downloads |
| `config.py` | Sample sizes, input limits, constants |
| `test_drafting.py`, `test_app.py` | 21 automated tests |

## Demo script (2 minutes)
1. Click **Medium sample**, press **Draft**. Point at the five pieces and the fit checks.
2. Switch neckline to **Shallow round** and regenerate: the front bodice outline changes.
3. Drag **Sleeve puff** up and regenerate: the sleeve gets wider and the cap check changes.
4. Open the front bodice dot-to-dot instructions and the CSV.

## Honest limitations
- Formulas are heuristics, not validated patternmaking. No darts, no fitted back shaping.
- Sleeve and skirt are simplified; skirt gathering is a ratio, not a full gathering plan.
- PDFs are previews: print scale is not verified. Use the 10 cm scale bar to check.
- Make a toile before cutting real fabric.
