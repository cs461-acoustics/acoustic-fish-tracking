#run the trained model on unlabeled echograms and save its boxes as Label Studio pre-labels
#so labelers only have to fix boxes instead of drawing every one
#pass the image folder in when running (python prelabel.py new_images --weights models/yolo11n_fish.pt)
#then import the .json it makes into Label Studio (see the README for the local files setup)
import argparse
import json
from pathlib import Path

from count_fish import count

parser = argparse.ArgumentParser(description="Make Label Studio pre-labels from YOLO predictions.")
parser.add_argument("images", help="folder of echogram PNGs")
parser.add_argument("--weights", default="models/yolo11n_fish.pt")
parser.add_argument("-o", "--output", default="prelabels.json", help="Label Studio tasks file to write")
parser.add_argument("--conf", type=float, default=0.2, help="lower than for counting, deleting a wrong box is faster than drawing a missed one")
parser.add_argument("--url-prefix", default="/data/local-files/?d=",
                    help="how Label Studio finds the images, default is its local files serving")
parser.add_argument("--root", default=".", help="folder Label Studio's local files document root points at")
args = parser.parse_args()

root = Path(args.root).resolve()
tasks = []
for img in sorted(Path(args.images).glob("*.png")):
    im, boxes = count(img, args.weights, args.conf, iou=0.3)
    W, H = im.size

    #Label Studio wants boxes as percents of the image size, using the same names as our labeling project
    #(image field "Image", box tool "label" on "image", class "fish")
    result = []
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        result.append({
            "id": f"pred{i}",
            "from_name": "label", "to_name": "image", "type": "rectanglelabels",
            "original_width": W, "original_height": H, "image_rotation": 0,
            "value": {
                "x": 100 * x0 / W, "y": 100 * y0 / H,
                "width": 100 * (x1 - x0) / W, "height": 100 * (y1 - y0) / H,
                "rotation": 0, "rectanglelabels": ["fish"],
            },
        })

    #path relative to the document root, so the image URL works from Label Studio
    rel = img.resolve().relative_to(root).as_posix()
    tasks.append({
        "data": {"Image": args.url_prefix + rel},
        "predictions": [{"model_version": Path(args.weights).stem, "result": result}],
    })
    print(f"{img.name}: {len(result)} pre-labeled fish")

Path(args.output).write_text(json.dumps(tasks, indent=1))
print(f"wrote {args.output} ({len(tasks)} images)")
