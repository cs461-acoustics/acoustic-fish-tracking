#shared helpers for reading YOLO labels, matching boxes, and scoring counts
from pathlib import Path

#read a YOLO label file and convert each line to a pixel box (x0, y0, x1, y1)
def read_yolo(path, W, H):
    boxes = []
    for line in Path(path).read_text().split("\n"):
        p = line.split()
        if len(p) != 5:
            continue
        x, y, w, h = (float(v) for v in p[1:])
        boxes.append(((x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H))
    return boxes

#pair each image with its label file, Label Studio names labels <hash>-<image name>.txt
#so if the name doesn't match directly, match on the part after the first dash
def pair_labels(image_dir, label_dir):
    images = {p.stem: p for p in Path(image_dir).glob("*.png")}
    pairs = []
    for lf in sorted(Path(label_dir).glob("*.txt")):
        stem = lf.stem if lf.stem in images else lf.stem.split("-", 1)[-1]
        if stem in images:
            pairs.append((images[stem], lf))
        else:
            print(f"no image for {lf.name}, skipping")
    return pairs

#overlap between two boxes (intersection over union, 0 = none, 1 = identical)
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u else 0.0

#match predicted boxes to labeled boxes one to one, best overlaps first
#returns (true positives, false positives, missed fish)
def match(pred, gt, thr=0.3):
    pairs = sorted(((iou(p, g), i, j) for i, p in enumerate(pred) for j, g in enumerate(gt)), reverse=True)
    up, ug, tp = set(), set(), 0
    for v, i, j in pairs:
        if v < thr:
            break
        if i in up or j in ug:
            continue
        up.add(i); ug.add(j); tp += 1
    return tp, len(pred) - tp, len(gt) - tp

#print the count, count error, precision and recall for one image
def report(name, pred, gt):
    tp, fp, fn = match(pred, gt)
    p = tp / (tp + fp) if pred else 0
    r = tp / (tp + fn) if gt else 0
    print(f"{name}: count={len(pred)} labeled={len(gt)} count_error={len(pred) - len(gt):+d} "
          f"| box match IoU>=0.3: precision={p:.2f} recall={r:.2f}")
