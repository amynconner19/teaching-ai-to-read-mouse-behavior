# BIOMAP n8n integration

This directory contains the n8n orchestration layer for BIOMAP. It connects an n8n
trigger to the repository's top-level command-line interface:

```text
Manual or file trigger
        ↓
Execute Command
        ↓
biomap analyze <video_dir>
        ↓
existing BIOMAP pipeline
```

n8n does not implement feature calculations, pose estimation, classification, or any
other scientific analysis. The workflow delegates those operations to `biomap analyze`,
which orchestrates the existing DeepLabCut, BIOMAP, and SimBA scripts.

The n8n integration therefore requires the pipeline implementation—and its
`biomap analyze` CLI—to already be available in the checkout. Installing n8n alone does
not install or implement the BIOMAP pipeline.

## Contents

- `n8n_biomap_workflow.json` — importable two-node hackathon workflow.
- `setup/start_n8n_macos.sh` — portable macOS startup helper.
- `setup/environment.example` — example environment variables.
- `docs/BIOMAP_N8N_SETUP.md` — complete local setup and operating instructions.

## Fresh machine / first-time setup

For the complete path from a new checkout through the first workflow run, see
[Fresh machine / first-time setup](docs/BIOMAP_N8N_SETUP.md#fresh-machine--first-time-setup).
It covers Node.js 24, n8n, Miniforge, the required Conda environments, workflow import,
and common setup failures.

## Import the workflow

1. Start n8n using `n8n/setup/start_n8n_macos.sh`.
2. Open the local n8n editor URL printed in the terminal.
3. In n8n, choose **Import from File** from the workflow menu.
4. Select `n8n/n8n_biomap_workflow.json` from this repository.
5. Open **Run BIOMAP Pipeline** and confirm the video directory and desired flags.
6. Save the workflow and use **Test workflow** to start it manually.

The supplied workflow runs:

```bash
cd "$BIOMAP_REPO" && ./biomap analyze videos/ --resume
```

See [BIOMAP_N8N_SETUP.md](docs/BIOMAP_N8N_SETUP.md) for prerequisites, demo mode,
safe validation, and operational notes.
