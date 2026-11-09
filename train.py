#fine tune a small YOLO model on the tiled echograms (CPU is fine)
#pass the data.yaml from build_dataset.py in when running (python train.py dataset/data.yaml)
import argparse
from pathlib import Path
from ultralytics import YOLO

ap = argparse.ArgumentParser()
ap.add_argument("data"); ap.add_argument("--epochs", type=int, default=80)
ap.add_argument("--model", default="yolo11n.pt"); ap.add_argument("--imgsz", type=int, default=320)
ap.add_argument("--project", default="runs"); ap.add_argument("--name", default="fish")
a = ap.parse_args()

#use a full path since newer ultralytics nests relative paths under runs/detect/
project = Path(a.project).resolve()

#brightness is echo strength, so hue/saturation changes, vertical flips and rotation are turned off
YOLO(a.model).train(
    data=a.data, epochs=a.epochs, imgsz=a.imgsz, batch=8, device="cpu", workers=2,
    project=str(project), name=a.name, exist_ok=True,
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.1, flipud=0.0, fliplr=0.5, mosaic=1.0, degrees=0.0,
    max_det=300, patience=30, plots=True, verbose=False,
)
print("weights saved to", project / a.name / "weights" / "best.pt")
