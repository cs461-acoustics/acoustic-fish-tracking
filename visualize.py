#side by side picture for each image: labeled fish | YOLO predictions | threshold baseline
#pass the image and label folders in when running
#(python visualize.py training_data project_annotations_yolo/labels --weights best.pt)
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from common import read_yolo, pair_labels
from count_fish import count
from baseline_threshold import detect

#draw the boxes, the white line where the held out pings start, and a title bar
def panel(im, boxes, color, title, xmin):
    p = im.copy(); d = ImageDraw.Draw(p)
    for b in boxes:
        d.rectangle(b, outline=color, width=2)
    d.line([(xmin, 0), (xmin, p.size[1])], fill=(255, 255, 255), width=2)
    d.rectangle((0, 0, p.size[0], 22), fill=(0, 0, 0))
    d.text((6, 5), title, fill=color)
    return p

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("images"); ap.add_argument("labels"); ap.add_argument("--weights", required=True)
    ap.add_argument("--out", default="comparisons"); ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--xmin", type=float, default=448)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(exist_ok=True)

    #counts in the titles only include the held out pings (right of xmin)
    val = lambda bs: sum((b[0] + b[2]) / 2 >= a.xmin for b in bs)
    for image, labels in pair_labels(a.images, a.labels):
        im, pred = count(image, a.weights, a.conf, iou=0.3)
        gt = read_yolo(labels, *im.size)
        thr = detect(np.asarray(im))
        panels = [
            panel(im, gt, (0, 255, 0), f"labels: {val(gt)} fish", a.xmin),
            panel(im, pred, (255, 220, 0), f"YOLO conf {a.conf}: {val(pred)}", a.xmin),
            panel(im, thr, (255, 0, 255), f"threshold: {val(thr)}", a.xmin),
        ]

        #paste the three panels next to each other with a small gap
        W, H = im.size; gap = 8
        sheet = Image.new("RGB", (3 * W + 2 * gap, H), (255, 255, 255))
        for i, p in enumerate(panels):
            sheet.paste(p, (i * (W + gap), 0))
        sheet.save(out / f"{image.stem}_compare.png")
        print("saved", out / f"{image.stem}_compare.png")
