# Risks

This is the project's only risk register. It covers business, technical, and team risks in one ranked list, plus every outside prerequisite the project waits on. We update it at every sprint planning and in the same pull request as any change that affects a risk.

Last reviewed 2026-11-01.

## Objective

By the end of spring term, deliver a fish counting model that links echosounder detections into tracks, beats a baseline tracker on held-out data, and comes with a documented codebase, report, and presentation.

## How we rank

Likelihood and impact are each high (H), medium (M), or low (L), judged against the objective above. The list is sorted with the highest risks at the top. We will act on the top five and watch the rest. When a risk’s trigger happens, we add it to the board as an issue and link the issue here.

Team roles are Marshall Arnold (PM), Gage Shinneman (AI Coordinator), Andrew Platt (Quality Owner), and Carter Deal (Documentationn Owner).

## Open risks

### R-1. We haven't secured the dataset we will build on

| | |
| --- | --- |
| Category | Business |
| Rank | H/H. We have to find the data ourselves, and the objective depends on it. |
| Statement | We haven't settled on the exact dataset we will build and test on. If we don't pick one soon, we will be behind, and the final model may be tested on data unlike what the project is meant for. |
| Owner | Marshall Arnold |
| Response | Mitigate. Make a short list of candidate datasets and figure out or ask the advisors which one fits the project best. |
| Trigger | No dataset chosen by 2026-11-20. |
| Contingency | Start on Forland dataset T2023002 (Salmon pen, stationary), which its authors describe as well suited for single-target detection and tracking. |
| Asked | Not yet. Start by 2026-11-09. |

### R-2. Our tracker may not beat the baseline on crossings

| | |
| --- | --- |
| Category | Technical |
| Rank | M/H. This is part of the core research question, and it is untested. |
| Statement | The project description says existing trackers often fail when fish cross or pass close together, and we haven’t built or tested our approach yet. |
| Owner | Gage Shinneman |
| Response | Mitigate. Figure out the baseline first, and keep crossings and dense cases as their own test set so we can see early where the model wins or loses. |
| Trigger | The first model scores no better than the baseline on the crossing test set. |
| Contingency | Report where it fails and narrow the claim to the densities where it does better. |
| Asked | Not needed. |

### R-3. Teammates may label the same tracks differently

| | |
| --- | --- |
| Category | Technical |
| Rank | M/H. Multiple people will label, and there is no labeling guide yet. |
| Statement | No dataset we've found comes with track labels, so we label tracks ourselves. If teammates label the same crossing differently, the evaluation numbers will measure our disagreement instead of the model. |
| Owner | Carter Deal |
| Response | Mitigate. Write a short labeling guide, have everyone label the same small sample first, and compare the results before labeling the rest. |
| Trigger | Two labelers disagree on more than 1 in 10 tracks in the shared sample. |
| Contingency | Revise the guide and relabel the sample before going further. |
| Asked | Not needed. |

### R-4. AI-written code could hide mistakes

| | |
| --- | --- |
| Category | Technical |
| Rank | M/M. We may use AI tools to help write code, and there are no automated tests yet. |
| Statement | The team may use AI tools to help write code, and CI and tests aren't set up yet. If AI-written code with a mistake gets merged, counts and metrics could be wrong without anyone noticing. |
| Owner | Andrew Platt |
| Response | Mitigate. Set up CI with tests on small made-up data, and have a teammate review every pull request, following the rules in AGENTS.md. |
| Trigger | CI isn't running by 2026-11-30, or a pull request that changes counting or metrics needs to be merged. |
| Contingency | Stop merging changes to counting and metrics code until it has tests. |
| Asked | Not needed. |

### R-5. Finals and winter break fall before the mid year checkpoint

| | |
| --- | --- |
| Category | Team |
| Rank | M/M. The dates are fixed and known ahead of time. |
| Statement | Finals week and winter break come right before the mid year checkpoint, and advisor replies may slow down over break. If work stops for those weeks, the mid year dataset and model will likely slip. |
| Owner | Marshall Arnold |
| Response | Mitigate. Plan the sprint around finals so data loading and labeling are done, and send any questions for the advisors before finals week. |
| Trigger | A question to the advisors is still open when finals week starts. |
| Contingency | Use the first week of winter term to catch up. |
| Asked | Not needed. |

### R-6. We may need more computing power than our laptops

| | |
| --- | --- |
| Category | Technical |
| Rank | L/M. The data size and compute needs are unknown. |
| Statement | We haven't estimated what training will need, and if it needs more than our personal computers, we need an OSU HPC account, which may take time to get. |
| Owner | Gage Shinneman |
| Response | Accept for now, because a first test would be cheap. Time one training run on a small sample once the dataset is chosen. |
| Trigger | A training run on the sample takes more than a few hours on a laptop. |
| Contingency | Request an OSU HPC account and train on a smaller sample until it comes through. |
| Asked | Not yet. Start by 2026-12-01. |

## Outside prerequisites

Each of these waits on someone outside the team. Nobody has asked yet, so each one has a start-by date. Once asked, the date is replaced with who asked, who they asked, and when.

| Prerequisite | Waits on | Owner | Asked, or start by |
| --- | --- | --- | --- |
| Advisor input on which dataset fits best (R-1) | Advisors (Lavery, Daly, Lalo) | Marshall Arnold | Start by 2026-11-09 |
| OSU HPC account, if R-6 says we need one | OSU HPC | Gage Shinneman | Start by 2026-12-01 | |

## Closed

- Team repository. The team created it.
- Partner data rules. The partners have no rules on storing or sharing the data.
