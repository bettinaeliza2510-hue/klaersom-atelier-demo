"""KlærSøm Flask app: form -> drafting engine -> plots and downloads.

Everything runs offline. Reference images and results live only in memory
(the 12 most recent designs) and are never written to disk.
"""
import csv
import io
import secrets
from collections import OrderedDict

from flask import Flask, abort, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

import config
from drafting import classify_body_type, draft_dress, point_rows
from plotting import combined_pdf, create_figure, figure_bytes

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
STORE = OrderedDict()
MAX_STORED = 12
MIMES = {"png": "image/png", "pdf": "application/pdf", "svg": "image/svg+xml"}


def defaults():
    return {**config.PRESETS["medium"], **config.DEFAULT_OPTIONS}


def validate(form):
    """Return ({name: float}, [error messages]) for every numeric field."""
    values, errors = {}, []
    for name, (low, high) in config.RANGES.items():
        label = name.replace("_", " ")
        try:
            value = float(form.get(name, "").strip())
        except ValueError:
            errors.append(f"Please enter a valid number for {label}.")
            continue
        if not low <= value <= high:        # also rejects NaN and infinity
            errors.append(f"{label.capitalize()} must be between {low} and {high}.")
            continue
        values[name] = round(value, 2)
    if form.get("neckline") not in config.NECKLINES:
        errors.append("Choose a supported neckline.")
    if form.get("skirt_style") not in config.SKIRTS:
        errors.append("Choose a supported skirt style.")
    if {"bust", "waist"} <= values.keys() and values["waist"] > values["bust"] * 1.25:
        errors.append("Please check the waist relative to the bust.")
    if {"hip", "waist"} <= values.keys() and values["waist"] > values["hip"] * 1.25:
        errors.append("Please check the waist relative to the hip.")
    return values, errors


def sniff_image(data):
    """Identify PNG/JPEG/WEBP by file signature (a signature check, not a full decode)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def read_reference(upload, errors):
    if not upload or not upload.filename:
        return None
    data = upload.read()
    mime = sniff_image(data) if data else None
    if not mime:
        errors.append("Upload a real PNG, JPG or WEBP image (the file could not be recognised).")
        return None
    return {"bytes": data, "mime": mime, "name": secure_filename(upload.filename)}


def coordinates_csv(pieces):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["piece", "point", "type", "x_cm", "y_cm", "meaning"])
    for p in pieces:
        for label, (x, y), is_key in zip(p["labels"], p["outline"], p["is_key"]):
            writer.writerow([p["name"], label, "key point" if is_key else "curve dot",
                             f"{x:.2f}", f"{y:.2f}", p["desc"].get(label, "")])
    return buf.getvalue().encode("utf-8-sig")      # BOM so Excel shows accents correctly


def build_result(m, form_options, image):
    dress = draft_dress(m, neckline=form_options["neckline"], skirt_style=form_options["skirt_style"],
                        skirt_fullness=m["skirt_fullness"], puff_fullness=m["puff_fullness"],
                        seam_allowance=m["seam_allowance"])
    pieces, figures = dress["pieces"], []
    for p in pieces:
        fig = create_figure(p)
        figures.append(fig)
        p["png"], p["pdf"], p["svg"] = (figure_bytes(fig, f) for f in ("png", "pdf", "svg"))
    token = secrets.token_urlsafe(12)
    STORE[token] = {"pieces": pieces, "image": image, "all_pdf": combined_pdf(figures),
                    "csv": coordinates_csv(pieces)}
    while len(STORE) > MAX_STORED:
        STORE.popitem(last=False)
    return {
        "token": token, "checks": dress["checks"], "body_type": classify_body_type(m),
        "allowance": m["seam_allowance"], "hem_allowance": dress["hem_allowance"],
        "neckline": config.NECKLINES[form_options["neckline"]], "skirt": config.SKIRTS[form_options["skirt_style"]],
        "reference": image["name"] if image else None,
        "pieces": [{"index": i, "name": p["name"], "cut": p["cut"], "dims": p["dims"], "segments": p["segments"],
                    "key_points": point_rows(p)[0], "dots": point_rows(p)[1]} for i, p in enumerate(pieces)],
    }


def get_saved(token):
    saved = STORE.get(token)
    if not saved:
        abort(404)
    return saved


@app.errorhandler(413)
def too_large(_):
    return render_template("index.html", presets=config.PRESETS, values=defaults(), config=config,
                           errors=["The image is larger than the 8 MB upload limit."], result=None), 413


@app.route("/", methods=["GET", "POST"])
def index():
    values, errors, result = defaults(), [], None
    if request.method == "POST":
        values.update({k: request.form.get(k, v) for k, v in values.items()})
        measurements, errors = validate(request.form)
        image = read_reference(request.files.get("reference_image"), errors)
        if not errors:
            try:
                result = build_result(measurements, values, image)
            except ValueError as exc:
                errors.append(f"Could not draft this pattern: {exc}")
    return render_template("index.html", presets=config.PRESETS, values=values, config=config,
                           errors=errors, result=result)


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/reference/<token>")
def reference(token):
    image = get_saved(token)["image"]
    if not image:
        abort(404)
    return send_file(io.BytesIO(image["bytes"]), mimetype=image["mime"])


@app.route("/plot/<token>/<int:i>")
def plot(token, i):
    pieces = get_saved(token)["pieces"]
    if not 0 <= i < len(pieces):
        abort(404)
    return send_file(io.BytesIO(pieces[i]["png"]), mimetype="image/png")


@app.route("/download/<token>/<int:i>/<fmt>")
def download(token, i, fmt):
    pieces = get_saved(token)["pieces"]
    if fmt not in MIMES or not 0 <= i < len(pieces):
        abort(404)
    return send_file(io.BytesIO(pieces[i][fmt]), mimetype=MIMES[fmt], as_attachment=True,
                     download_name=f"klarsom_{pieces[i]['id']}.{fmt}")


@app.route("/download/<token>/all.pdf")
def download_all(token):
    return send_file(io.BytesIO(get_saved(token)["all_pdf"]), mimetype="application/pdf",
                     as_attachment=True, download_name="klarsom_all_pieces.pdf")


@app.route("/download/<token>/coordinates.csv")
def download_csv(token):
    return send_file(io.BytesIO(get_saved(token)["csv"]), mimetype="text/csv",
                     as_attachment=True, download_name="klarsom_coordinates.csv")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
