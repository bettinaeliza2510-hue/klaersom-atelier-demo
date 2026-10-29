"""KlærSøm dress-drafting engine.

Units are centimetres. x grows to the right, y grows DOWN the pattern (towards the hem).
Every piece is drawn from a single origin at its top-left, with the centre-front /
centre-back / fold edge on x = 0.

IMPORTANT: these are educational heuristics, not professionally validated patterns.
Make a toile (test garment) before cutting final fabric.
"""
from math import hypot

from config import HEM_ALLOWANCE

DROP = 2.5                 # shoulder slope: shoulder tip sits this far below the neck point
FRONT_NECK_DEPTH = {"square": 8.5, "shallow": 7.0}
BACK_NECK_DEPTH = 3.0


# ---------------------------------------------------------------- geometry helpers
def dist(p, q):
    """Straight-line distance between two points (Pythagoras)."""
    return hypot(q[0] - p[0], q[1] - p[1])


def bezier(p0, ctrl, p1, n):
    """n points strictly between p0 and p1 on a quadratic Bezier curve.

    A Bezier is a smooth curve pulled towards the control point `ctrl`;
    it is how we draw armholes, round necklines and the sleeve cap.
    """
    pts = []
    for i in range(1, n + 1):
        t = i / (n + 1)
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * ctrl[0] + t * t * p1[0],
                    u * u * p0[1] + 2 * u * t * ctrl[1] + t * t * p1[1]))
    return pts


def polygon_area(poly):
    """Shoelace formula."""
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
                   for i in range(n))) / 2


def _side(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def self_intersects(poly):
    """True if any two non-neighbouring edges of a closed outline cross."""
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue   # these two edges share a vertex
            c, d = poly[j], poly[(j + 1) % n]
            if _side(a, c, d) * _side(b, c, d) < 0 and _side(a, b, c) * _side(a, b, d) < 0:
                return True
    return False


def offset_polygon(vertices, allowances):
    """Push every edge of a closed outline outwards and re-join the shifted edges.

    `allowances` is one number or one number per edge (edge i runs from point i to
    point i+1). A fold edge gets 0, a seam gets the seam allowance, a hem a bigger one.
    """
    n = len(vertices)
    if n < 3:
        raise ValueError("A pattern outline needs at least 3 points.")
    if isinstance(allowances, (int, float)):
        allowances = [allowances] * n
    if len(allowances) != n or min(allowances) < 0:
        raise ValueError("Seam allowances must be non-negative, one per edge.")
    # Shoelace sign tells us the winding direction, hence which side is "outside".
    signed = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1]))
    if abs(signed) < 1e-8:
        raise ValueError("Pattern outline has zero area.")
    shifted = []   # (point on shifted edge, edge direction, outward unit normal, allowance)
    for i in range(n):
        (x1, y1), (x2, y2) = vertices[i], vertices[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        length = hypot(dx, dy)
        if length < 1e-8:
            raise ValueError("Repeated adjacent points.")
        nx, ny = (dy / length, -dx / length) if signed > 0 else (-dy / length, dx / length)
        a = allowances[i]
        shifted.append(((x1 + nx * a, y1 + ny * a), (dx, dy), (nx, ny), a))
    result = []
    for i in range(n):
        p0, (ax, ay), _, _ = shifted[i - 1]          # previous shifted edge
        q0, (bx, by), (nx, ny), a = shifted[i]       # this shifted edge
        det = ax * by - ay * bx
        if abs(det) < 1e-9:                          # edges are collinear: just slide the point out
            result.append((vertices[i][0] + nx * a, vertices[i][1] + ny * a))
            continue
        # Intersection of the two shifted lines (Cramer's rule).
        t = ((q0[0] - p0[0]) * by - (q0[1] - p0[1]) * bx) / det
        result.append((p0[0] + t * ax, p0[1] + t * ay))
    return result


# ---------------------------------------------------------------- piece building
class Outline:
    """Builds a closed outline from labelled key points and curves."""

    def __init__(self, label, xy):
        self.pts = [(label, xy, True, None)]   # (label, (x, y), is_key_point, kind of edge arriving here)

    def line(self, label, xy, kind="seam"):
        self.pts.append((label, xy, True, kind))
        return self

    def curve(self, label, ctrl, xy, kind="seam", n=6):
        """Smooth curve from the previous key point; its dots are labelled e.g. C1..C6."""
        prev_label, prev_xy = self.pts[-1][0], self.pts[-1][1]
        for i, q in enumerate(bezier(prev_xy, ctrl, xy, n), 1):
            self.pts.append((f"{prev_label}{i}", q, False, kind))
        self.pts.append((label, xy, True, kind))
        return self


def _piece(pid, name, cut, o, closing, dims, desc):
    labels = [p[0] for p in o.pts]
    xy = [p[1] for p in o.pts]
    is_key = [p[2] for p in o.pts]
    return {
        "id": pid, "name": name, "cut": cut, "labels": labels, "outline": xy, "is_key": is_key,
        "kinds": [p[3] for p in o.pts[1:]] + [closing],      # kind of edge i -> i+1
        "points": {l: p for l, p, k in zip(labels, xy, is_key) if k},
        "dims": dims, "desc": desc,
    }


def path_length(piece, a, b):
    """Length of the outline from point label a to point label b (following curves)."""
    labels, pts = piece["labels"], piece["outline"]
    n, i, j, total = len(pts), labels.index(a), labels.index(b), 0.0
    while i != j:
        total += dist(pts[i], pts[(i + 1) % n])
        i = (i + 1) % n
    return total


def _direction(dx, dy):
    if abs(dx) < 1e-8:
        return "down" if dy >= 0 else "up"
    if abs(dy) < 1e-8:
        return "right" if dx >= 0 else "left"
    return f"diagonally {'down' if dy >= 0 else 'up'}-{'right' if dx >= 0 else 'left'}"


def instructions(piece):
    """Dot-to-dot sentences a tailor can follow with a ruler on newspaper."""
    pts, labels, kinds = piece["outline"], piece["labels"], piece["kinds"]
    keys = [i for i, k in enumerate(piece["is_key"]) if k]
    out = []
    for k, a in enumerate(keys):
        b = keys[(k + 1) % len(keys)]
        dots = labels[a + 1:b] if b > a else []
        d = dist(pts[a], pts[b])
        if dots:
            text = (f"From {labels[a]}, draw a smooth curve through dots {dots[0]}-{dots[-1]} "
                    f"to {labels[b]} ({d:.1f} cm apart in a straight line).")
        else:
            text = f"From {labels[a]}, measure {d:.1f} cm {_direction(pts[b][0] - pts[a][0], pts[b][1] - pts[a][1])} to {labels[b]}."
        if kinds[a] == "fold":
            text += " This edge is the fold."
        out.append(text)
    return out


def point_rows(piece):
    """(key_point_rows, curve_dot_rows) for tables and CSV."""
    keys, dots = [], []
    for l, (x, y), k in zip(piece["labels"], piece["outline"], piece["is_key"]):
        (keys if k else dots).append({"label": l, "x": x, "y": y, "desc": piece["desc"].get(l, "")})
    return keys, dots


# ---------------------------------------------------------------- the pieces
def _bodice_frame(m):
    bust, waist, shoulder = float(m["bust"]), float(m["waist"]), float(m["shoulder_width"])
    bust_width = bust / 4 + 1.0           # quarter bust + 1 cm: half-piece width (4 cm total ease)
    waist_width = waist / 4 + 0.5         # quarter waist + 0.5 cm (2 cm total ease)
    armhole_depth = bust / 6 + 7          # classic heuristic: one-sixth bust + 7 cm
    shoulder_x = min(shoulder / 2, bust_width - 1)   # half the shoulder width = shoulder tip
    return bust_width, waist_width, armhole_depth, shoulder_x


def _neck_width(m, neckline):
    bust, shoulder = float(m["bust"]), float(m["shoulder_width"])
    base = bust / 10 if neckline == "square" else bust / 12 + 0.5
    return min(base, shoulder / 2 - 1)    # never wider than the shoulder allows


def _check_bodice(neck_w, shoulder_x, armhole_depth, length):
    if neck_w <= 0 or shoulder_x - neck_w < 2:
        raise ValueError("Shoulder width is too small for this neckline.")
    if length < armhole_depth + 3:
        raise ValueError("Front length is too short for the armhole depth of this bust size.")


def draft_front_bodice(m, neckline="square"):
    bw, ww, ad, sx = _bodice_frame(m)
    length, nw, nd = float(m["front_length"]), _neck_width(m, neckline), FRONT_NECK_DEPTH[neckline]
    _check_bodice(nw, sx, ad, length)
    desc = {"A": "Centre-front neckline", "N": "Neck-shoulder point", "C": "Shoulder tip",
            "D": "Underarm (side seam)", "E": "Waist (side seam)", "F": "Centre-front waist"}
    o = Outline("A", (0.0, nd))
    if neckline == "square":
        o.line("B", (nw, nd)).line("N", (nw, 0.0))
        desc["B"] = "Square neckline corner"
    else:   # control point 0.914 of the way out makes a quarter-ellipse look
        o.curve("N", (0.914 * nw, 0.914 * nd), (nw, 0.0))
    o.line("C", (sx, DROP))
    o.curve("D", (sx - 1.0, DROP + 0.75 * (ad - DROP)), (bw, ad))   # front armhole bows inwards
    o.line("E", (ww, length)).line("F", (0.0, length))
    dims = {"bust_width": round(bw, 1), "waist_width": round(ww, 1), "armhole_depth": round(ad, 1),
            "neck_width": round(nw, 1), "neck_depth": round(nd, 1), "front_length": round(length, 1)}
    return _piece("front_bodice", "Front bodice (half)", "Cut 1 on the fold", o, "fold", dims, desc)


def draft_back_bodice(m, neckline="square"):
    """Back uses the same neck width (so shoulder seams match) but a shallow neckline."""
    bw, ww, ad, sx = _bodice_frame(m)
    length, nw, nd = float(m["front_length"]), _neck_width(m, neckline), BACK_NECK_DEPTH
    _check_bodice(nw, sx, ad, length)
    o = Outline("A", (0.0, nd))
    o.curve("N", (0.914 * nw, 0.914 * nd), (nw, 0.0))
    o.line("C", (sx, DROP))
    o.curve("D", (sx - 0.5, DROP + 0.70 * (ad - DROP)), (bw, ad))   # back armhole is a little flatter
    o.line("E", (ww, length)).line("F", (0.0, length))
    desc = {"A": "Centre-back neckline", "N": "Neck-shoulder point", "C": "Shoulder tip",
            "D": "Underarm (side seam)", "E": "Waist (side seam)", "F": "Centre-back waist"}
    dims = {"bust_width": round(bw, 1), "waist_width": round(ww, 1), "neck_depth": round(nd, 1),
            "back_length": round(length, 1)}
    return _piece("back_bodice", "Back bodice (half)", "Cut 2, one reversed (centre-back seam)", o, "seam", dims, desc)


def draft_skirt(m, style="gathered_a_line", fullness=1.8):
    waist, hip = float(m["waist"]), float(m["hip"])
    skirt_length = float(m["dress_length"]) - float(m["front_length"])   # shoulder-to-hem minus bodice
    if skirt_length < 10:
        raise ValueError("Dress length must be at least 10 cm longer than the front length.")
    base_top = waist / 4 + 0.5            # same width as the bodice waist
    hip_width = hip / 4 + 1.0             # quarter hip + 1 cm ease
    if style == "gathered_a_line":
        top = base_top * fullness         # fullness ratio = how much the waist edge is gathered
        hem = max(hip_width, top + 10.0)  # hem flares wider than the waist
    else:
        top, fullness = base_top, 1.0
        hem = max(hip_width, top)         # never narrower than the hip
    o = Outline("A", (0.0, 0.0)).line("B", (top, 0.0)).line("C", (hem, skirt_length)).line("D", (0.0, skirt_length), "hem")
    desc = {"A": "Centre waist (on fold)", "B": "Waist side seam", "C": "Hem side seam", "D": "Centre hem (on fold)"}
    dims = {"top_width": round(top, 1), "hem_width": round(hem, 1), "skirt_length": round(skirt_length, 1),
            "fullness_ratio": round(fullness, 2)}
    return _piece("skirt", "Skirt panel (half)", "Cut 2 on the fold (front and back)", o, "fold", dims, desc)


def draft_sleeve(m, puff=1.5):
    bust, upper_arm, shoulder = float(m["bust"]), float(m["upper_arm"]), float(m["shoulder_width"])
    cap_h = (bust / 6 + 7) / 3            # sleeve cap height ~ one third of armhole depth
    width = (upper_arm + 4.0) * puff      # arm + 4 cm ease, multiplied by the puff ratio
    length = max(12.0, shoulder * 0.42)   # short sleeve: underarm length from shoulder width
    o = Outline("A", (0.0, cap_h))
    o.curve("B", (width * 0.12, 0.0), (width / 2, 0.0))
    o.curve("C", (width * 0.88, 0.0), (width, cap_h))
    o.line("D", (width, cap_h + length)).line("E", (0.0, cap_h + length))
    desc = {"A": "Underarm corner", "B": "Cap peak: match to shoulder seam", "C": "Underarm corner",
            "D": "Hem corner", "E": "Hem corner"}
    dims = {"sleeve_width": round(width, 1), "cap_height": round(cap_h, 1),
            "sleeve_length": round(length, 1), "puff_ratio": round(puff, 2)}
    return _piece("sleeve", "Short puff sleeve", "Cut 2 (gather cap and hem)", o, "seam", dims, desc)


def draft_sash(m):
    length, width = float(m["waist"]) * 2.0, 10.0    # two waist lengths leaves room for a bow
    o = Outline("A", (0.0, 0.0)).line("B", (length, 0.0)).line("C", (length, width)).line("D", (0.0, width))
    desc = {"A": "Corner", "B": "Corner", "C": "Corner", "D": "Corner"}
    return _piece("sash", "Waist sash", "Cut 2, sew right sides together and turn out", o, "seam",
                  {"sash_length": round(length, 1), "sash_width": width}, desc)


# ---------------------------------------------------------------- checks and assembly
def fit_checks(m, pieces):
    """Plain-language consistency checks between pieces (not a substitute for a fitting)."""
    by = {p["id"]: p for p in pieces}
    f, b, s, sl = by["front_bodice"], by["back_bodice"], by["skirt"], by["sleeve"]
    checks = []

    def add(label, value, ok, note):
        checks.append({"label": label, "value": value, "status": "ok" if ok else "warn", "note": note})

    sh_f, sh_b = dist(f["points"]["N"], f["points"]["C"]), dist(b["points"]["N"], b["points"]["C"])
    add("Shoulder seam, front vs back", f"{sh_f:.1f} / {sh_b:.1f} cm", abs(sh_f - sh_b) <= 0.3,
        "These two edges are sewn together, so they must be the same length.")
    sd_f, sd_b = dist(f["points"]["D"], f["points"]["E"]), dist(b["points"]["D"], b["points"]["E"])
    add("Side seam, front vs back", f"{sd_f:.1f} / {sd_b:.1f} cm", abs(sd_f - sd_b) <= 0.3,
        "Front and back side seams are sewn together.")
    bust_ease = 4 * f["dims"]["bust_width"] - float(m["bust"])
    add("Ease at bust", f"+{bust_ease:.1f} cm", 2 <= bust_ease <= 10, "Room to breathe and move; fitted dresses usually need 2-8 cm.")
    waist_ease = 4 * f["dims"]["waist_width"] - float(m["waist"])
    add("Ease at waist", f"+{waist_ease:.1f} cm", 0 <= waist_ease <= 8, "Total bodice waist minus your waist measurement.")
    ratio = s["dims"]["top_width"] / f["dims"]["waist_width"]
    add("Skirt gathering ratio", f"{ratio:.2f} : 1", 1.0 <= ratio <= 2.5,
        "Skirt waist edge divided by bodice waist edge; 1 means no gathers.")
    armhole = path_length(f, "C", "D") + path_length(b, "C", "D")
    cap = path_length(sl, "A", "C")
    cap_ratio = cap / armhole
    add("Sleeve cap vs armhole", f"{cap:.1f} vs {armhole:.1f} cm ({cap_ratio:.2f} : 1)", 1.0 <= cap_ratio <= 1.8,
        "Puff sleeves need a cap 1.1-1.7x the armhole so it can be gathered in; below 1 it will not reach round.")
    return checks


def draft_dress(m, neckline="square", skirt_style="gathered_a_line", skirt_fullness=1.8,
                puff_fullness=1.5, seam_allowance=1.5):
    """Draft all five pieces, add cutting lines, validate geometry, return pieces + checks."""
    m = {k: float(v) for k, v in m.items()}
    pieces = [draft_front_bodice(m, neckline), draft_back_bodice(m, neckline),
              draft_skirt(m, skirt_style, skirt_fullness), draft_sleeve(m, puff_fullness), draft_sash(m)]
    allowance = {"seam": seam_allowance, "fold": 0.0, "hem": max(HEM_ALLOWANCE, seam_allowance)}
    for p in pieces:
        if self_intersects(p["outline"]):
            raise ValueError(f"{p['name']}: the outline crosses itself. Check the measurements.")
        p["cut_outline"] = offset_polygon(p["outline"], [allowance[k] for k in p["kinds"]])
        if self_intersects(p["cut_outline"]):
            raise ValueError(f"{p['name']}: the seam allowance folds over itself. Try a smaller allowance.")
        p["segments"] = instructions(p)
    return {"pieces": pieces, "checks": fit_checks(m, pieces), "hem_allowance": allowance["hem"]}


def classify_body_type(m):
    """Simple proportion label, not a definitive body-type classification."""
    bust, waist, hip = (float(m[k]) for k in ("bust", "waist", "hip"))
    balance = abs(bust - hip) / max(bust, hip)
    if balance <= .05 and waist / bust <= .75 and waist / hip <= .75:
        return "Hourglass-like"
    if hip > bust * 1.05:
        return "Pear / triangle-like"
    if bust > hip * 1.05:
        return "Inverted-triangle-like"
    return "Balanced proportions"
