#baseline fish counter, keep the bright pixels and count each connected blob as one fish
#pass the image in when running (python baseline_threshold.py <image> --labels <labels.txt>)
#add --xmin 448 to only score the held out pings (same as count_fish.py)
import argparse
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from common import read_yolo, report

def detect(rgb, surface_rows=0, min_area=12, thresh=150, close=2):
    #labeled fish peak around 150-220 gray and background is mostly under 150
    mask = rgb[..., :3].astype(int).mean(axis=2) >= thresh

    #skip the noisy band at the top (off by default)
    mask[:surface_rows] = False

    #close small gaps so a broken up fish trace becomes one blob
    if close:
        mask = ndimage.binary_closing(mask, structure=np.ones((close * 2 + 1, close * 2 + 1)))

    #group touching pixels into blobs and drop tiny ones as noise
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    boxes = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        area = int((lab[sl] == i).sum())
        if area < min_area:
            continue
        y, x = sl
        boxes.append((x.start, y.start, x.stop, y.stop))
    return boxes

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("--labels"); ap.add_argument("--out")
    ap.add_argument("--surface-rows", type=int, default=0)
    ap.add_argument("--thresh", type=int, default=150, help="gray level (0-255) counted as a strong echo")
    ap.add_argument("--min-area", type=int, default=12)
    ap.add_argument("--xmin", type=float, default=0)
    a = ap.parse_args()
    im = Image.open(a.image).convert("RGB")

    #only keep blobs and labels right of xmin (the held out pings)
    inside = lambda b: (b[0] + b[2]) / 2 >= a.xmin
    boxes = [b for b in detect(np.asarray(im), a.surface_rows, a.min_area, a.thresh) if inside(b)]
    gt = [b for b in read_yolo(a.labels, *im.size) if inside(b)] if a.labels else []
    print(f"fish count (threshold baseline): {len(boxes)}")
    if a.labels:
        report("threshold", boxes, gt)

    #save an overlay, labels in green, blobs in yellow
    if a.out:
        d = ImageDraw.Draw(im)
        for bx in gt:
            d.rectangle(bx, outline=(0, 255, 0))
        for bx in boxes:
            d.rectangle(bx, outline=(255, 255, 0))
        im.save(a.out)
