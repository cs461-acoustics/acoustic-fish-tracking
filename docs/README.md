# acoustic-fish-tracking

This project explores the use of AI and machine learning to estimate mesopelagic fish abundance from broadband echosounder data collected by autonomous, moored acoustic platforms. These systems continuously record echoes from fish and zooplankton, generating massive acoustic datasets that can reveal population dynamics and behavior at unprecedented temporal scales. A key challenge is accurately associating individual detections across successive pings to maintain fish identities when trajectories intersect, overlap, or temporarily merge, situations that often cause traditional tracking methods to fail. The goal of this project is to create a computer vision model that can associate fish tracks for fish counting. 

This repository currently provides tools for downloading and organizing acoustic datasets and generating summary statistics from raw recording files, plus a first fish counting pipeline: a YOLO object detector trained on hand-labeled echograms, and a simple brightness-threshold baseline to compare it against. This is the foundation for future machine learning models that can improve fish counting, track disambiguation, and 3D trajectory reconstruction.

## Installation

Clone this repo and run the following commands to download the necessary libraries.

```bash
pip install boto3 echopype matplotlib
```

For the fish counting pipeline, install its requirements (ultralytics also installs PyTorch):

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 dataset_pull.py <bucket> <prefix> <destination_directory>
python3 transducer_settings.py <path_to_raw_file>
python3 plot_echogram.py <path_to_raw_file> [-o output.png]
```

## Fish Counting Pipeline

The pipeline uses the labeled echograms in `training_data/` (grayscale 70 kHz PNGs) and their YOLO-format box labels in `project_annotations_yolo/labels/`, exported from Label Studio.

| File | What it does |
|---|---|
| `build_dataset.py` | Splits each echogram by time (first 70% of pings for training, last 30% held out) and cuts it into overlapping 320 px tiles for YOLO |
| `train.py` | Fine-tunes a YOLO11 detector on the tiles (YOLO11n by default, runs on CPU) |
| `count_fish.py` | Counts fish in a full echogram with the trained model, and scores it against labels if given |
| `baseline_threshold.py` | Baseline counter: keeps bright pixels and counts each connected blob as one fish |
| `visualize.py` | Saves side-by-side pictures of the labels, model predictions, and threshold baseline |
| `common.py` | Shared helpers for reading labels, pairing them with images, and scoring |

Build the dataset and train:

```bash
python3 build_dataset.py training_data project_annotations_yolo/labels dataset
python3 train.py dataset/data.yaml
```

Weights are saved to `runs/fish/weights/best.pt`. Use `--model yolo11s.pt` to try the larger model.

The trained YOLO11n model behind the results below is committed at `models/yolo11n_fish.pt`, so you can count fish without training. Swap in `runs/fish/weights/best.pt` to use your own run.

Count and score one echogram on its held-out pings (`--xmin 448` keeps only the last 30% of a 640 px image):

```bash
python3 count_fish.py training_data/<image>.png --weights models/yolo11n_fish.pt --conf 0.25 --labels project_annotations_yolo/labels/<label>.txt --xmin 448
python3 baseline_threshold.py training_data/<image>.png --labels project_annotations_yolo/labels/<label>.txt --xmin 448
```

Make comparison pictures for every labeled image (saved to `comparisons/`):

```bash
python3 visualize.py training_data project_annotations_yolo/labels --weights models/yolo11n_fish.pt
```

First results on the held-out pings of the six labeled echograms (267 labeled fish): YOLO11n at confidence 0.25 counted 262 fish, found 72% of the labeled fish, and 73% of its detections were real fish. The threshold baseline counted 118 and found 5-34% per image. These numbers are a first estimate, since the test pings come from the same recordings used for training.
## CI Testing

At our current stage, we have little to do CI tests on because we are primarily doing data exploration. In the future, CI testing will look like ensuring the pipeline from data ingestion to model output runs without failing. 

## Contributing

This is an ongoing project. Pull requests are closed to only current contributors.

## License

[MIT](https://choosealicense.com/licenses/mit/)
