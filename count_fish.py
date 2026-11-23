#count fish in an echogram image with a trained YOLO model
#pass the image and weights in when running (python count_fish.py <image> --weights best.pt)
#add --labels <labels.txt> to score it, and --xmin 448 to only score the held out pings
import argparse
import math
from PIL import Image, ImageDraw
from ultralytics import YOLO
from common import read_yolo, report

def count(image, weights, conf=0.35, iou=0.3, surface_rows=0, contain=0.5):
    im = Image.open(image).convert("RGB")

    #run at the image's own size so fish look the same size as in training
    sz = int(math.ceil(max(im.size) / 32) * 32)
    r = YOLO(weights).predict(im, imgsz=sz, conf=conf, iou=iou, max_det=1000, device="cpu", verbose=False)[0]

    #skip anything in the noisy band at the top (off by default)
    boxes = [tuple(b) for b in r.boxes.xyxy.tolist() if (b[1] + b[3]) / 2 > surface_rows]
    return im, drop_contained(boxes, r.boxes.conf.tolist(), contain)

#drop a box if most of it sits inside a stronger box (usually a piece of the same fish trace)
def drop_contained(boxes, scores, frac):
    order = sorted(range(len(boxes)), key=lambda i: -scores[i]) if len(scores) == len(boxes) else range(len(boxes))
    keep = []
    for i in order:
        a = boxes[i]; area = (a[2] - a[0]) * (a[3] - a[1])
        inside = False
        for k in keep:
            ix = max(0, min(a[2], k[2]) - max(a[0], k[0])); iy = max(0, min(a[3], k[3]) - max(a[1], k[1]))
            if area and ix * iy / area > frac:
                inside = True; break
        if not inside:
            keep.append(a)
    return keep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("--weights", required=True)
    ap.add_argument("--conf", type=float, default=0.35); ap.add_argument("--labels")
    ap.add_argument("--iou", type=float, default=0.3, help="NMS overlap; lower merges more duplicates")
    ap.add_argument("--contain", type=float, default=0.5, help="drop boxes this much inside a stronger one")
    ap.add_argument("--surface-rows", type=int, default=0, help="ignore detections centered in the top N rows")
    ap.add_argument("--xmin", type=float, default=0); ap.add_argument("--out")
    a = ap.parse_args()
    im, boxes = count(a.image, a.weights, a.conf, a.iou, a.surface_rows, a.contain)

    #only keep fish right of xmin (the held out pings)
    inside = lambda b: (b[0] + b[2]) / 2 >= a.xmin
    boxes = [b for b in boxes if inside(b)]
    print(f"fish count (YOLO): {len(boxes)}")

    #score against the labels if given
    gt = [b for b in read_yolo(a.labels, *im.size) if inside(b)] if a.labels else []
    if a.labels:
        report("yolo", boxes, gt)

    #save an overlay, labels in green, predictions in yellow
    if a.out:
        d = ImageDraw.Draw(im)
        for b in gt: d.rectangle(b, outline=(0, 255, 0))
        for b in boxes: d.rectangle(b, outline=(255, 255, 0))
        if a.xmin: d.line([(a.xmin, 0), (a.xmin, im.size[1])], fill=(255, 255, 255))
        im.save(a.out)
