# Requirements
 
## Problem statement
 
Researchers at OSU and PNNL work with broadband echosounder data and want 
to count and track fish. The specific problem within this area is still 
being determined with our project partners.
 
## Functional requirements
 
- FR-1 (Must: nothing else runs without data; assumed) `in progress`:
  The pipeline downloads every file under a given bucket and prefix from a
  public S3 bucket without credentials into a local directory, keeping
  relative paths. Script: `dataset_pull.py`.
  Acceptance: for a prefix containing N files, N files exist locally at the
  matching relative paths; a prefix with no files prints a message and exits
  without error.
- FR-2 (Must: Sv is the input to everything downstream; assumed)
  `in progress`: Given an EK80 `.raw` file, the pipeline computes calibrated
  Sv, preferring broadband complex data and falling back to CW complex, then
  CW power, and reports which mode it used. Script: `plot_echogram.py`.
  Acceptance: on the CW sample file, Sv is produced and the reported mode is
  a CW mode; if no mode works, the run reports the failure for each attempt.
- FR-3 (Should: lets the team look at the data; assumed) `in progress`: The
  pipeline saves an echogram image (PNG) for one channel. Script:
  `plot_echogram.py`. Today the channel and range window are hardcoded;
  which ones matter is open (OQ-3).
  Acceptance: on the sample file, a non-empty PNG is written to the requested
  output path.
  
## Non-functional requirements
 
- NFR-1 (Must: others must be able to run it; assumed) `not built`: A fresh
  clone runs the pipeline end to end on the sample dataset with one
  documented command, and the dependencies are installed from a file in the
  repository.
- NFR-2 (Should: CI has no display; assumed) `not built`: The scripts run to
  completion without a display attached. Acceptance: runs with a
  non-interactive plotting backend and exits zero.

## Constraints
 
- C-1: Python, with echopype for reading and processing echosounder data.
- C-2: Data comes from the NCEI water column sonar archive (the
  `noaa-wcsd-pds` bucket), unless other data is provided.
- C-3: There is no trusted labeled baseline: only unlabeled echosounder data
  is available. This limits how results can be validated.
  
## Success metrics

All thresholds are proposed starting points, `assumed` until confirmed.
 
- Reproducibility: the end-to-end run on the sample dataset passes in CI on
  every merge to the default branch.
- Synthetic track recovery: on a fixed test set with fish-like tracks
  injected at known times and depths into real echosounder data, the pipeline
  recovers at least 80% of injected tracks (proposed) with at most <N> false
  tracks per hour of data.
  
## Open questions
 
- OQ-1: What decision will the output feed (a count, track catalog, etc.)
  and what do we consider a useful result? Owner: TBD. Answer by: End of first term
- OQ-2: Ground truth and labeling strategy: how do we validate without
  trusted labels, given we do not know how many track-crossing events
  exist? Owner: TBD. Answer by: End of first term
