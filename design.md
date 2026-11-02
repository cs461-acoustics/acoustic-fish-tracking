Autonomous, moored broadband echosounders continuously record echoes from individual mesopelagic fish and other zooplankton, generating millions of per-ping target detections over multi-year deployments. Converting these detections into individual fish trajectories requires associating detections across successive pings into continuous 3D tracks that capture each animal's swimming behavior.
Existing tracking approaches perform well when fish are sparse and well-separated, but break down in the common case where two or more tracks intersect, cross closely in range/angle, or temporarily merge into a single overlapping echo before diverging again. When tracks cross, conventional methods can swap fish identities, fragment true trajectories, or fail to re-establish tracks after separation, corrupting downstream behavioral and abundance analyses.
This goal of this capstone project, co-advised by Dr. Andone Lavery (OSU), Dr. Marg Daly (PNNL), and Nick Lalo (PNNL), is to design and implement an AI/ML-based approach to count fish from broadband echosounders. Students will work with real detection datasets from operational moorings to determine the fish counts and potentially generate trajectories that are visualized as 3D point tracks over time (position vs. time, per axis).
Problem statement
Mesopelagic fish (small, deep-dwelling species) are now understood to be among the most abundant vertebrate groups on Earth, with global biomass estimates likely exceeding the combined weight of all other fish stocks in the ocean. Despite this staggering abundance, they remain one of the least understood components of the marine ecosystem, largely because their depth, patchiness, and the sheer difficulty of sampling them directly make traditional survey methods (trawling, visual census) poorly suited to studying them at scale. Mesopelagic assemblages play an outsized role in global ocean function. They are an important mid-food-web link, consuming zooplankton and in turn supporting commercially and ecologically important predators such as tunas, billfish, seabirds, and marine mammals.
Because direct sampling is so limited, broadband active acoustics from moored platforms and autonomous underwater vehicles are two of the few tools capable of observing these animals continuously, in situ, and at the scale their patchy, highly mobile populations demand. But the scientific value of that acoustic record depends on being able to resolve individual animals within it: how many fish are present, how they move, whether they aggregate or school, and how they respond to one another and to predators. That resolution is exactly what breaks down when fish tracks cross or overlap, which is common in the dense assemblages that make mesopelagic biomass so significant in the first place. Improving track disambiguation therefore directly improves our ability to characterize assemblage-level abundance, behavior, and ecological role — the central open questions motivating this research.

This project explores the use of AI and machine learning to estimate mesopelagic fish abundance from broadband echosounder data collected by autonomous, moored acoustic platforms. These systems continuously record echoes from fish and zooplankton, generating massive acoustic datasets that can reveal population dynamics and behavior at unprecedented temporal scales. A key challenge is accurately associating individual detections across successive pings to maintain fish identities when trajectories intersect, overlap, or temporarily merge, situations that often cause traditional tracking methods to fail. This repository currently provides tools for downloading and organizing acoustic datasets and generating summary statistics from raw recording files, establishing the foundation for future development of machine learning models that can improve fish counting, track disambiguation, and 3D trajectory reconstruction. By enabling more reliable estimates of mesopelagic fish abundance and movement, this work supports broader efforts to understand the ecological role of one of the ocean's most abundant and least-studied vertebrate communities.






Write me a design.md file in this format based on the above and the context about my current progress:


# Design



## Overview
Shift board for <partner> (requirements: docs/requirements.md): a React
front end, a Node API, and Postgres on Render, behind Google Workspace SSO.



## Architecture
![C4 context diagram](./diagrams/context.png)
![C4 container diagram](./diagrams/containers.png)
- Web app (React): the board, the claim and release flows.
- API (Node, Express): auth check, shift rules, notifications.
- Postgres, managed by Render: shifts, claims, users.
- Email (Postmark), called from the API on release.



## Interfaces
- REST, JSON (ADR-002). Spec in docs/api/openapi.yaml; the client is
  generated from it. POST /shifts/{id}/claims returns 409 when the shift is full.



## Data
- Postgres through Prisma (ADR-001): User, Shift, Claim (ERD in
  ./diagrams/erd.png). One Claim per (shift, user), enforced by a
  database constraint.



## Deployment
- Render web service plus managed Postgres; a preview deploy per PR.
- Production: the partner's Render account, owned by their IT lead.
  Their security sign-off is R-2 in the risk register, docs/risks.md.
  ADR-004.
- Rollback: redeploy the previous build (tried once, works).



## Open questions
- SSO on the partner's Workspace tenant is unproven; Priya spikes it first.
- Can Postmark send from the partner's domain without DNS changes on
  their side? Spike it before building the release emails.



## Deferred decisions
- Notification delivery: email from the API for now; a queue only if
  volume calls for one, recorded in an ADR when it does.




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
