#cut labeled echograms into overlapping tiles and split train/val by time (x axis)
#pass a whole folder (python build_dataset.py training_data project_annotations_yolo/labels dataset)
#or a single image (python build_dataset.py <image> <labels.txt> <out folder>)
import argparse
from pathlib import Path
from PIL import Image
from common import read_yolo, pair_labels

#top left corners of every tile, adding one more at the edge so nothing gets left out
def tiles(W, H, t, s):
    xs = list(range(0, max(W - t, 0) + 1, s)) or [0]
    ys = list(range(0, max(H - t, 0) + 1, s)) or [0]
    if xs[-1] + t < W: xs.append(W - t)
    if ys[-1] + t < H: ys.append(H - t)
    return [(x, y) for y in ys for x in xs]

def build(image, labels, out_dir, tile, stride, val_frac):
    im = Image.open(image).convert("RGB"); W, H = im.size
    boxes = read_yolo(labels, W, H)

    #the last val_frac of the pings (right side) is held out so val fish are never seen in training
    split_x = int(W * (1 - val_frac))
    out = Path(out_dir); stem = Path(image).stem
    parts = {"train": im.crop((0, 0, split_x, H)), "val": im.crop((split_x, 0, W, H))}
    offs = {"train": 0, "val": split_x}
    for split, part in parts.items():
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)
        pw, ph = part.size; n_t = n_b = 0
        for tx, ty in tiles(pw, ph, tile, stride):
            tw, th = min(tile, pw), min(tile, ph)
            lines = []

            #move each box into tile coordinates and clip it to the tile edge
            for x0, y0, x1, y1 in boxes:
                x0, x1 = x0 - offs[split] - tx, x1 - offs[split] - tx
                y0, y1 = y0 - ty, y1 - ty
                cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x1, tw), min(y1, th)
                if cx1 <= cx0 or cy1 <= cy0:
                    continue

                #drop slivers, boxes with less than 40% left inside the tile
                if (cx1 - cx0) * (cy1 - cy0) < 0.4 * (x1 - x0) * (y1 - y0):
                    continue
                lines.append(f"0 {(cx0+cx1)/2/tw:.6f} {(cy0+cy1)/2/th:.6f} {(cx1-cx0)/tw:.6f} {(cy1-cy0)/th:.6f}")

            #save the tile image and its label file
            name = f"{stem}_{split}_x{tx}_y{ty}"
            part.crop((tx, ty, tx + tw, ty + th)).save(out / "images" / split / f"{name}.png")
            (out / "labels" / split / f"{name}.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
            n_t += 1; n_b += len(lines)
        print(f"{stem} {split}: {n_t} tiles, {n_b} boxes (pings x {offs[split]}..{offs[split]+pw})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("labels"); ap.add_argument("out")
    ap.add_argument("--tile", type=int, default=320); ap.add_argument("--stride", type=int, default=160)
    ap.add_argument("--val-frac", type=float, default=0.3)
    a = ap.parse_args()

    #if given folders, pair up every image with its labels, otherwise just use the one image
    pairs = pair_labels(a.image, a.labels) if Path(a.image).is_dir() else [(a.image, a.labels)]
    for image, labels in pairs:
        build(image, labels, a.out, a.tile, a.stride, a.val_frac)

    #write the data.yaml that tells YOLO where the tiles are
    out = Path(a.out)
    (out / "data.yaml").write_text(f"path: {out.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: fish\n")
    print(f"wrote {out/'data.yaml'}")

if __name__ == "__main__":
    main()
