# Design
 
## Overview
 
Mesopelagic Fish Counting and Tracking is a research-focused machine learning project that aims to estimate fish abundance and reconstruct individual fish trajectories from broadband echosounder data collected by autonomous, moored acoustic platforms. The project supports ongoing research at Oregon State University (OSU) and Pacific Northwest National Laboratory (PNNL) by providing tools to process acoustic datasets, generate exploratory statistics, and establish a foundation for AI/ML-based fish counting and track disambiguation. Current development is focused on dataset acquisition, acoustic file processing, and statistical characterization of recordings before implementing trajectory reconstruction and machine learning models.
 
## Architecture
 
- Dataset acquisition scripts download and organize broadband echosounder datasets from NOAA research vessel EK-80 transducers.
- Acoustic processing utilities load and inspect raw acoustic recording files.
- Analysis scripts compute information about channel settings and exploratory metrics from recordings.
- Visualization tools generate plots for dataset exploration.
- Future ML pipeline will ingest processed detections and estimate fish counts while resolving track crossings and overlapping targets.
- Future trajectory generation module will produce 3D fish tracks over time for visualization and behavioral analysis.
 
## Interfaces
 
- Python-based command-line workflows for dataset download and processing.
- Acoustic data processed using scientific Python libraries and broadband sonar processing tools (e.g., Echopype).
- Analysis outputs include channel settings, visualizations, and derived datasets for downstream machine learning workflows.
- Future interfaces may include configuration files and model inference pipelines for batch processing deployments.
 
## Data
 
- Broadband echosounder recordings collected from autonomous moored platforms.
- Raw acoustic files are stored and processed locally before feature extraction and analysis.
- Current derived data products include recording-level settings information and exploratory visualizations.
- Future data products will include fish detections, trajectory associations, estimated fish counts, and reconstructed 3D movement tracks.
 
## Deployment
 
- Development currently runs locally using Python-based analysis workflows.
- Source code is managed through Git and hosted in a public repository.
- Data processing is designed to support large acoustic datasets generated from long-term deployments.
- Future deployment may include reproducible training and inference environments for machine learning model evaluation and operational processing.
 
## Open Questions
 
- Which machine learning approach is most effective for estimating fish abundance from broadband acoustic detections?
- How should crossing, overlapping, and merging fish tracks be represented to minimize identity switching?
- What acoustic features provide the strongest signal for distinguishing individual fish in dense assemblages?
- What evaluation metrics best measure counting accuracy and trajectory reconstruction performance?
 
## Deferred Decisions
 
- Selection of the final machine learning architecture.
- Real-time versus batch-processing workflows.
- Long-term storage strategy for derived detections and trajectory outputs.
- Interactive visualization tools for exploring reconstructed fish tracks and abundance estimates.
