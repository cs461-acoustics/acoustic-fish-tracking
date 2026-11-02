Context for AI coding tools working in this repository.
This file is the single source of AI context for the repo. Tool-specific files (CLAUDE.md, .github/copilot-instructions.md, .cursor/rules/, etc.) must only point here, for example a CLAUDE.md containing the one line See AGENTS.md. Do not copy content from this file into them.
Owner: AI Coordinator, currently Gage Shinneman.

Project context
We are an Oregon State University EECS capstone team building an AI/ML approach for counting fish from broadband echosounder detections.
Data. Autonomous moored broadband echosounders record echoes from individual mesopelagic fish and zooplankton. The data is real and imperfect.
Core problem. Associating detections across successive pings into continuous tracks. Existing trackers work when fish are sparse but fail when tracks cross.
Goals.
Mid-year: prepared training/evaluation dataset and a first model.
Final: a fish counting model with quantitative performance metrics on held-out data, compared against a baseline tracker. Also, a documented, working codebase, plus a final report and presentation.
Stack and conventions
Currently, there is no code yet.
Language: Python
Environment / packaging / libraries: tbd
Tests: tbd, the commands live in CONTRIBUTING.md.
Branching, PRs, and review: see CONTRIBUTING.md.
Definition of Done: see CONTRIBUTING.md.
How AI tools should behave here
Keep changes small and scoped to one issue.
Ask (or leave a TODO(question)) rather than guessing about units, coordinate frames, or detection field meanings.
Confidentiality boundary
All data used in this project is from public databases, so there are no restrictions there.
When unsure whether something may go into a tool, do not paste it, ask the AI Coordinator first.
To be added once code exists
Repository layout: what each top-level directory holds
Detection data schema: fields, units, coordinate frame, time base
Environment / packaging / libraries
