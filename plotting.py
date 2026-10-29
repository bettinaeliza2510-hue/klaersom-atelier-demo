"""Draws pattern pieces. Uses Figure directly (not pyplot) so it is safe inside Flask threads."""
from io import BytesIO

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

BURGUNDY, GOLD, INK = "#6d3859", "#b38b4d", "#27283d"


def create_figure(piece):
    pts, cut = piece["outline"], piece["cut_outline"]
    xs, ys = [p[0] for p in pts + cut], [p[1] for p in pts + cut]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0, y1 - y0
    size = (10, max(2.8, 10 * h / w + 2.2)) if h / w < 0.5 else (7, min(10, 7 * h / w + 1.8))

    fig = Figure(figsize=size)
    ax = fig.add_subplot(111)
    px, py = [p[0] for p in pts], [p[1] for p in pts]
    ax.fill(px, py, facecolor="#f6ecf0", edgecolor=BURGUNDY, linewidth=2, label="Stitching line")
    ax.plot([p[0] for p in cut] + [cut[0][0]], [p[1] for p in cut] + [cut[0][1]],
            linestyle="--", color=GOLD, linewidth=1.6, label="Cutting line")

    n = len(pts)
    for i, kind in enumerate(piece["kinds"]):      # thick line + word marks the fold edge
        if kind == "fold":
            a, b = pts[i], pts[(i + 1) % n]
            ax.plot([a[0], b[0]], [a[1], b[1]], color=INK, linewidth=4, solid_capstyle="butt")
            ax.text((a[0] + b[0]) / 2 + 0.6, (a[1] + b[1]) / 2, "FOLD", rotation=90, va="center", fontsize=8, color=INK)

    for label, (x, y), is_key in zip(piece["labels"], pts, piece["is_key"]):
        if is_key:
            ax.plot(x, y, "o", color=BURGUNDY, markersize=5)
            ax.annotate(label, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=10, fontweight="bold", color=INK)
        else:
            ax.plot(x, y, ".", color=GOLD, markersize=5)

    cx, cy = (min(px) + max(px)) / 2, (min(py) + max(py)) / 2     # grainline arrow through the middle
    if (max(px) - min(px)) > 3 * (max(py) - min(py)):
        half = (max(px) - min(px)) * 0.2
        ax.annotate("", (cx + half, cy), (cx - half, cy), arrowprops=dict(arrowstyle="<->", color=INK))
        ax.text(cx, cy - 0.9, "grainline", ha="center", fontsize=8, color=INK)
    else:
        half = (max(py) - min(py)) * 0.2
        ax.annotate("", (cx, cy + half), (cx, cy - half), arrowprops=dict(arrowstyle="<->", color=INK))
        ax.text(cx + 0.6, cy, "grainline", rotation=90, va="center", fontsize=8, color=INK)

    bar = 10 if w >= 14 else 5                                     # scale bar below the piece
    ax.plot([x0, x0 + bar], [y1 + 1.8, y1 + 1.8], color=INK, linewidth=3)
    ax.text(x0 + bar + 0.6, y1 + 1.8, f"{bar} cm", va="center", fontsize=8, color=INK)

    step = 1 if max(w, h) <= 50 else 5 if max(w, h) <= 120 else 10
    ax.xaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.grid(True, linestyle=":", linewidth=.5, alpha=.7)
    ax.set_xlim(x0 - 1.5, x1 + 1.5)
    ax.set_ylim(y1 + 3.5, y0 - 1.5)                                # inverted: y grows downwards
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(labelsize=7)
    ax.set_xlabel("cm from origin", fontsize=8)
    ax.set_title(f"{piece['name']}: {piece['cut']}", fontsize=11, color=BURGUNDY)
    ax.legend(loc="best", fontsize=8, framealpha=.9)
    fig.text(0.5, 0.005, "Preview only: use the scale bar, print scale is not verified.", ha="center", fontsize=7, color="#777184")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return fig


def figure_bytes(fig, fmt):
    buf = BytesIO()
    fig.savefig(buf, format=fmt, dpi=160, bbox_inches="tight")
    return buf.getvalue()


def combined_pdf(figs):
    """One PDF with a page per pattern piece."""
    buf = BytesIO()
    with PdfPages(buf) as pdf:
        for fig in figs:
            pdf.savefig(fig, bbox_inches="tight")
    return buf.getvalue()
