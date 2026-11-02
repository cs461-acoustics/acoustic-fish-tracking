# acoustic-fish-tracking

This project explores the use of AI and machine learning to estimate mesopelagic fish abundance from broadband echosounder data collected by autonomous, moored acoustic platforms. These systems continuously record echoes from fish and zooplankton, generating massive acoustic datasets that can reveal population dynamics and behavior at unprecedented temporal scales. A key challenge is accurately associating individual detections across successive pings to maintain fish identities when trajectories intersect, overlap, or temporarily merge, situations that often cause traditional tracking methods to fail. The goal of this project is to create a computer vision model that can associate fish tracks for fish counting. 

This repository currently provides tools for downloading and organizing acoustic datasets and generating summary statistics from raw recording files, establishing the foundation for dataset generation for future machine learning models that can improve fish counting, track disambiguation, and 3D trajectory reconstruction.

## Installation

Clone this repo and run the following commands to download the necessary libraries.

```bash
pip install boto3 echopype matplotlib
```

## Usage

```bash
python3 dataset_pull.py <bucket> <prefix> <destination_directory>
python3 transducer_settings.py <path_to_raw_file>
python3 plot_echogram.py <path_to_raw_file> [-o output.png]
```
## CI Testing

At our current stage, we have little to do CI tests on because we are primarily doing data exploration. In the future, CI testing will look like ensuring the pipeline from data ingestion to model output runs without failing. 

## Contributing

This is an ongoing project. Pull requests are closed to only current contributors.

## License

[MIT](https://choosealicense.com/licenses/mit/)