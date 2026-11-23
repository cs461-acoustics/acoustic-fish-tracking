"""
fish_stamp_sim.py -- Synthetic echogram generator.

Idea: don't simulate the instrument, just paint fish directly onto the
image grid.  One fish = a small pattern ("stamp"):
  * vertical profile  = a sinc, plus a weaker, slightly delayed second sinc
  * along the ping axis = a boomerang, brightness fading as a Gaussian
  * a complex amplitude (random phase), so that overlapping fish ADD as amplitudes:
    they can reinforce (brighter) or cancel (dark gaps), not just get brighter
  * optional tilt (slope) so a whole school can drift upward across the image


Usage
  python fish_stamp_sim.py --n 5 --seed 0 --outdir out_v0
  python fish_stamp_sim.py --demo                  # 4-panel figure for advisors
  python fish_stamp_sim.py --check                 # self-tests
  python fish_stamp_sim.py --background crop.png   # add onto a real 640x640 fish-free crop

Knobs: sinc width `w` and delay `d` (box height), arch width
`arch_sw` and curvature `k` (box width/shape), `peak_db` (max gray inside boxes ->
Sv = -70 + 60*gray/255), fish per image, school size/slope, overlap frequency.
School slope sign: negative = rows decrease with column. Which physical direction that is
depends on whether the sonar looks up or down, so flip with --slope if needed.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import numpy as np

H = W = 640
VMIN, VMAX = -70.0, -10.0
DB_FLOOR = -120.0


@dataclass
# Note: These parameters may be overwritten by the rand_fish() function, which draws them from a random distribution.
class Fish:
    row: float                # row of the arch apex (closest approach), pixels
    col: float                # column of the apex
    peak_db: float            # peak Sv of this fish alone (dB)
    k: float = 0.06           # arch curvature: row offset = k * dc^2
    slope: float = 0.0        # tilt of arch axis, rows per column (school drift)
    arch_sw: float = 4.0      # Gaussian half-width of brightness along the arch (columns)
    w: float = 2.0            # sinc width in rows (first zero at +-w)
    d: float = 2.0            # delay of the second sinc (rows)
    g: float = 0.5            # amplitude ratio of the second sinc
    phase: float = 0.0        # overall phase (radians)
    phase2: float = 0.0       # extra phase of the second sinc
    fringe_px: float = 4.0    # carrier period in rows (makes overlap interference stripes)
    school: int = -1          # school id, -1 = isolated fish


# ------------------------------------------------------------------ the stamp
def stamp(f: Fish):
    """Complex patch for one fish. Returns (row_offset, col_offset, patch)."""
    half = int(np.ceil(3.0 * f.arch_sw))
    c_lo = int(np.floor(f.col)) - half
    cols = np.arange(c_lo, c_lo + 2 * half + 1)
    dc = cols - f.col
    rc = f.row + f.slope * dc + f.k * dc ** 2             # center row at each column
    pad = int(np.ceil(6 * f.w + abs(f.d))) + 2
    r_lo = int(np.floor(rc.min())) - pad
    rows = np.arange(r_lo, int(np.ceil(rc.max())) + pad + 1)
    x = rows[:, None] - rc[None, :]                        # row distance to this fish's center
    env = np.exp(-dc ** 2 / (2 * f.arch_sw ** 2))[None, :]
    prof = np.sinc(x / f.w) + f.g * np.sinc((x - f.d) / f.w) * np.exp(1j * f.phase2)
    xs = np.linspace(-8 * f.w, 8 * f.w + abs(f.d), 4001)
    pmax = np.abs(np.sinc(xs / f.w) + f.g * np.sinc((xs - f.d) / f.w) * np.exp(1j * f.phase2)).max()
    carrier = np.exp(1j * (f.phase + 2 * np.pi * x / f.fringe_px))   # phase relative to own center
    return r_lo, c_lo, 10 ** (f.peak_db / 20) / pmax * env * prof * carrier


# ------------------------------------------------------------------ rendering
def render(fishes, h=H, w=W, background_db=None, coherent=True, box_drop_db=12.0):
    """Paint fish into an (h, w) Sv image in dB. Returns (db_image, boxes).

    coherent=True : complex amplitudes add (reinforce / cancel)
    coherent=False: intensities add (what a naive 'brighter where they overlap' would give)
    """
    acc = np.zeros((h, w), complex if coherent else float)
    boxes = []
    for i, f in enumerate(fishes):
        r_lo, c_lo, P = stamp(f)
        r0, r1 = max(r_lo, 0), min(r_lo + P.shape[0], h)
        c0, c1 = max(c_lo, 0), min(c_lo + P.shape[1], w)
        if r0 >= r1 or c0 >= c1:
            continue
        sub = P[r0 - r_lo:r1 - r_lo, c0 - c_lo:c1 - c_lo]
        acc[r0:r1, c0:c1] += sub if coherent else np.abs(sub) ** 2
        own_db = 20 * np.log10(np.abs(sub) + 1e-12)
        m = own_db >= max(f.peak_db - box_drop_db, VMIN)   # visible part of THIS fish
        if m.any():
            ys, xs = np.nonzero(m)
            boxes.append(dict(fish_id=i, x=int(c0 + xs.min()), y=int(r0 + ys.min()),
                              w=int(xs.max() - xs.min() + 1), h=int(ys.max() - ys.min() + 1),
                              peak_db=float(f.peak_db), school=int(f.school)))
    inten = np.abs(acc) ** 2 if coherent else acc
    if background_db is not None:
        inten = inten + 10 ** (background_db / 10)
    db = 10 * np.log10(np.maximum(inten, 10 ** (DB_FLOOR / 10)))
    mark_overlaps(boxes)
    return db, boxes


def mark_overlaps(boxes):
    for b in boxes:
        b["overlaps_other"] = False
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            p, q = boxes[i], boxes[j]
            if (p["x"] < q["x"] + q["w"] and q["x"] < p["x"] + p["w"]
                    and p["y"] < q["y"] + q["h"] and q["y"] < p["y"] + p["h"]):
                p["overlaps_other"] = q["overlaps_other"] = True


def to_gray(db):
    return np.clip((db - VMIN) / (VMAX - VMIN), 0, 1)


def load_background_db(path, h=H, w=W):
    """Gray PNG -> Sv dB using the same mapping as the training images."""
    from PIL import Image
    g = np.array(Image.open(path).convert("L"), float)
    if g.shape != (h, w):
        raise ValueError(f"background must be {h}x{w}, got {g.shape}")
    return VMIN + (VMAX - VMIN) * g / 255.0


# ------------------------------------------------------------------ scene generator
def rand_fish(rng, row, col, peak_db, slope=0.0, school=-1):
    # TUNE PARAMETERS. These are rough estimates for now.

    fish_slope = slope + rng.normal(0, 0.20)

    return Fish(row=row, col=col, peak_db=peak_db, k=rng.uniform(0.0, 0.06), slope=fish_slope,
                arch_sw=rng.uniform(2.0, 9.0), w=rng.uniform(1.0, 2.5), d=rng.uniform(1.0, 3.0),
                g=rng.uniform(0.3, 0.7), phase=rng.uniform(0, 2 * np.pi),
                phase2=rng.uniform(0, 2 * np.pi), school=school)


def make_scene(rng, n_static=20, n_schools=1.0, slope=-0.25, school_size=(8, 30),
               peak_static=(-42.0, 5.0), peak_school=(-45.0, 4.0), h=H, w=W, margin=20):
    fishes = []
    for _ in range(rng.poisson(n_static)):
        fishes.append(rand_fish(rng, rng.uniform(margin, h - margin), rng.uniform(margin, w - margin),
                                rng.normal(*peak_static)))
    for s in range(rng.poisson(n_schools)):
        n = int(rng.integers(school_size[0], school_size[1] + 1))
        cr, cc = rng.uniform(4 * margin, h - 4 * margin), rng.uniform(4 * margin, w - 4 * margin)

        # Shared orientation for this school
        school_slope = slope + rng.normal(0, 0.15)
        for _ in range(n):
            fishes.append(rand_fish(rng, cr + rng.normal(0, 12), cc + rng.normal(0, 25),
                                    rng.normal(*peak_school), slope=school_slope,
                                    school=s))
    return fishes


# ------------------------------------------------------------------ output
def save_yolo_labels(outdir, stem, boxes, img_w=W, img_h=H):
    """
    Save bounding boxes in YOLO format:
    class_id x_center y_center width height

    All coordinates are normalized to [0, 1].
    """
    os.makedirs(outdir, exist_ok=True)

    label_path = os.path.join(outdir, f"{stem}.txt")

    with open(label_path, "w") as f:
        for b in boxes:
            x_center = (b["x"] + b["w"] / 2) / img_w
            y_center = (b["y"] + b["h"] / 2) / img_h
            width = b["w"] / img_w
            height = b["h"] / img_h

            class_id = 0  # fish

            f.write(
                f"{class_id} {x_center:.6f} {y_center:.6f} "
                f"{width:.6f} {height:.6f}\n"
            )

def save_scene(outdir, stem, db, boxes, fishes, split="train"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    image_dir = os.path.join(outdir, "images", split)
    label_dir = os.path.join(outdir, "labels", split)

    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(label_dir, exist_ok=True)

    # Save clean grayscale image
    plt.imsave(
        os.path.join(image_dir, f"{stem}.png"),
        to_gray(db),
        cmap="gray",
        vmin=0,
        vmax=1
    )

    # Save YOLO annotations
    save_yolo_labels(
        label_dir,
        stem,
        boxes,
        db.shape[1],
        db.shape[0]
    )



# ------------------------------------------------------------------ self-tests
def run_checks():
    ok = True

    def report(name, passed, detail):
        nonlocal ok
        ok &= bool(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

    base = dict(row=30.0, col=50.0, k=0.05, g=0.0, arch_sw=5.0, phase2=0.0)
    db, _ = render([Fish(peak_db=-40.0, **base)], 64, 100)
    report("single fish peak equals peak_db", abs(db.max() + 40) < 0.05, f"max = {db.max():.2f} dB")

    same, _ = render([Fish(peak_db=-40.0, phase=0.0, **base), Fish(peak_db=-40.0, phase=0.0, **base)], 64, 100)
    canc, _ = render([Fish(peak_db=-40.0, phase=0.0, **base), Fish(peak_db=-40.0, phase=np.pi, **base)], 64, 100)
    report("equal phases reinforce (+6 dB)", abs(same.max() - (-40 + 6.02)) < 0.05, f"max = {same.max():.2f} dB")
    report("opposite phases cancel", canc.max() < -100, f"max = {canc.max():.1f} dB")
    inc, _ = render([Fish(peak_db=-40.0, phase=0.0, **base), Fish(peak_db=-40.0, phase=np.pi, **base)],
                    64, 100, coherent=False)
    report("brightness-add mode ignores phase (+3 dB)", abs(inc.max() - (-40 + 3.01)) < 0.05,
           f"max = {inc.max():.2f} dB")

    f = Fish(row=50.0, col=100.0, peak_db=-40.0, k=0.0, slope=-0.3, g=0.0, arch_sw=40.0)
    db, _ = render([f], 100, 200)
    cols = np.arange(70, 131)
    rows = np.argmax(db[:, cols], axis=0)
    fit = np.polyfit(cols, rows, 1)[0]
    report("school tilt slope recovered", abs(fit + 0.3) < 0.02, f"fit slope = {fit:.3f} (want -0.300)")

    rng = np.random.default_rng(1)
    fishes = make_scene(rng, n_static=25, n_schools=2)
    db, boxes = render(fishes)
    inside = all(b["x"] <= round(fishes[b["fish_id"]].col) < b["x"] + b["w"]
                 and b["y"] <= round(fishes[b["fish_id"]].row) < b["y"] + b["h"] for b in boxes)
    report("every box contains its fish's apex", inside, f"{len(boxes)} boxes for {len(fishes)} fish")

    bg = np.full((64, 100), VMIN + 60 * 50 / 255)
    db, _ = render([Fish(peak_db=-30.0, **base)], 64, 100, background_db=bg)
    report("background shows through where no fish", abs(db[2, 2] - bg[2, 2]) < 0.05,
           f"{db[2, 2]:.2f} vs {bg[2, 2]:.2f} dB")
    print("ALL PASSED" if ok else "SOME FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Version 0 stamp-based synthetic echogram generator")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outdir", default="out_v0")
    ap.add_argument("--static", type=float, default=20, help="mean number of isolated fish")
    ap.add_argument("--schools", type=float, default=1.0, help="mean number of schools")
    ap.add_argument("--slope", type=float, default=-0.25, help="school drift, rows per column")
    ap.add_argument("--background", default=None, help="640x640 gray PNG (fish-free real crop)")
    ap.add_argument("--demo", action="store_true", help="write the 4-panel demo figure")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        raise SystemExit(0 if run_checks() else 1)
    if a.demo:
        os.makedirs(a.outdir, exist_ok=True)
        demo_figure(os.path.join(a.outdir, "demo_panels.png"))
        print("wrote", os.path.join(a.outdir, "demo_panels.png"))
        return
    bg = load_background_db(a.background) if a.background else None
    for k in range(a.n):
        rng = np.random.default_rng(a.seed + k)
        fishes = make_scene(rng, a.static, a.schools, a.slope)
        db, boxes = render(fishes, background_db=bg)
        stem = f"scene_seed{a.seed + k}"
        save_scene(a.outdir, stem, db, boxes, fishes)
        print(f"{stem}: {len(fishes)} fish ({sum(f.school >= 0 for f in fishes)} in schools), "
              f"{len(boxes)} boxes, {sum(b['overlaps_other'] for b in boxes)} overlapping")


if __name__ == "__main__":
    main()
