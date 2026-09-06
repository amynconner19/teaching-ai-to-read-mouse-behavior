# BIOMAP n8n DeepLabCut Runner

## What this does

This contribution provides a deliberately small, local n8n workflow for the
validated PawDigits DeepLabCut inference step:

```text
Click Execute workflow in self-hosted n8n
  → n8n launches Paw DeepLabCut
  → DeepLabCut analyzes each supported video in BIOMAP_VIDEO_DIR
  → live progress is written to dlc_live.log
```

The current workflow isolates **Paw DeepLabCut only** for stability testing.
Facial tracking, DLC merging, SimBA, and BIOMAP state routing are not invoked by
this workflow.

The Paw project is read from:

```text
deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml
```

The runner builds a disposable project mirror under the ignored
`n8n/biomap_pipeline/results/.work/` directory, so it does not rewrite the
checked-in scientific project. Verified CSVs are published under the ignored
`n8n/biomap_pipeline/results/tracking/paw/` directory.

## Prerequisites

- macOS or Linux shell
- Conda or Miniforge with `conda` on `PATH`
- self-hosted n8n
- a working `biomap-dlc` Conda environment
- the PawDigits DeepLabCut project and trained checkpoint present locally
- Git LFS model files materialized rather than pointer text
- at least one input AVI video in `BIOMAP_VIDEO_DIR`

DeepLabCut inference can take tens of minutes depending on the video and
hardware. The validated Mac default is CPU.

## Required environment variables

Set these before starting n8n:

```bash
export BIOMAP_REPO="/path/to/teaching-ai-to-read-mouse-behavior"
export BIOMAP_VIDEO_DIR="$BIOMAP_REPO/videos"
export BIOMAP_DLC_ENV="biomap-dlc"
export BIOMAP_DLC_DEVICE="cpu"
```

`BIOMAP_DLC_DEVICE` is passed directly to DeepLabCut. The runner never
auto-selects CUDA or MPS.

## Start n8n

From the repository root:

```bash
./n8n/setup/start_n8n_macos.sh
```

The helper preserves existing environment overrides and supplies portable
defaults derived from its own checkout location.

## Import the workflow

In the local n8n editor, choose **Import from File** and select:

```text
n8n/n8n_biomap_workflow.json
```

The imported workflow is named **BIOMAP DeepLabCut Runner**.

## Run

Open the workflow and click **Execute workflow**. The node chain is:

```text
Manual Trigger → Pipeline Inputs → Run DeepLabCut
```

`Run DeepLabCut` invokes `biomap dlc ... --resume`. A matching Paw CSV is
skipped only after validation; missing, malformed, partial, wrong-body-part, or
wrong-frame-count output is rerun.

## Watch progress

Portable command:

```bash
tail -f "$BIOMAP_REPO/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Development-machine example only (not used by code or workflow JSON):

```bash
tail -f "/Users/jkathila/Desktop/work/teaching-ai-to-read-mouse-behavior/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Expected output includes:

```text
[n8n] DeepLabCut command started
[DLC Paw] START
[Python] DeepLabCut imported
[DLC Paw] Analyzing videos with ...
[DLC Paw] Running pose prediction with batch size 8
[DLC Paw] 47/116451
```

## Troubleshooting

### `BIOMAP_DLC_ENV` is empty

Symptom from an unquoted or empty Conda environment argument:

```text
ArgumentError: Argument --name requires a value
```

Set and export the environment before starting n8n:

```bash
export BIOMAP_DLC_ENV="biomap-dlc"
```

The supplied workflow also fails immediately with a clear
`BIOMAP_DLC_ENV is required` message when the variable is absent.

### CUDA checkpoint cannot load on a Mac

Symptom:

```text
Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

Fix:

```bash
export BIOMAP_DLC_DEVICE="cpu"
```

`PYTORCH_ENABLE_MPS_FALLBACK=1` alone does not fix CUDA checkpoint
deserialization.

### Git LFS pointer files

If a required YAML or checkpoint begins with:

```text
version https://git-lfs.github.com/spec/v1
```

materialize the Paw project files from the repository root:

```bash
git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"
```

Do not commit the locally materialized files as part of the n8n contribution.

### The log file is blank

- Confirm the n8n execution is still active.
- Confirm the **Run DeepLabCut** command contains `2>&1 | tee`.
- Confirm `n8n/biomap_pipeline/results/logs/` exists and is writable.
- Confirm n8n was started with access to the required environment variables.

### AVI validation

AVI input is supported and the sample AVI was validated through OpenCV and a
real DeepLabCut CPU inference startup. The automated test suite never runs the
full video inference.

See [docs/BIOMAP_N8N_SETUP.md](docs/BIOMAP_N8N_SETUP.md) for clone-to-run setup
instructions.
