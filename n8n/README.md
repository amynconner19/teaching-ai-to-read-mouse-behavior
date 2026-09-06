# BIOMAP n8n DeepLabCut Runner

## What this does

A deliberately small, local n8n workflow for the validated PawDigits
DeepLabCut inference step:

```text
Click Execute workflow in self-hosted n8n
  → n8n launches Paw DeepLabCut
  → DeepLabCut analyzes each supported video in BIOMAP_VIDEO_DIR
  → live progress is written to dlc_live.log
```

## Scope

This workflow runs **Paw DeepLabCut only**. It does not run facial tracking,
the DLC merge, SimBA, ROI or calibration checks, or BIOMAP state routing. It is
not full BIOMAP automation.

The Paw project is read from:

```text
deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml
```

The runner builds a disposable project mirror under the ignored
`n8n/biomap_pipeline/results/.work/` directory, so it never rewrites the
checked-in scientific project. Verified CSVs are published under the ignored
`n8n/biomap_pipeline/results/tracking/paw/` directory.

## First-time setup checklist

```text
 1. Clone the repository
 2. Install Git LFS                     ← prerequisite, not installed by the script
 3. Install Miniforge/Conda             ← prerequisite, not installed by the script
 4. Install Node.js and n8n             ← prerequisite, not installed by the script
 5. Create or obtain the biomap-dlc env ← prerequisite, not installed by the script
 6. Materialize the PawDigits DeepLabCut model files
 7. Verify the AVI input is readable
 8. Run n8n/setup/start_n8n_macos.sh
 9. Import n8n/n8n_biomap_workflow.json into n8n
10. Click Execute workflow
11. Monitor dlc_live.log
```

Steps 2 through 5 are prerequisites you install yourself. The startup script
does not install them. Full instructions are in
[docs/BIOMAP_N8N_SETUP.md](docs/BIOMAP_N8N_SETUP.md).

## Verify prerequisites

None of these start inference:

```bash
git lfs version
conda env list
conda run -n biomap-dlc python -c 'import deeplabcut; print(deeplabcut.__version__)'
n8n --version
```

`conda env list` must include `biomap-dlc`.

## Materialize the Git LFS model files

The trained project is stored in Git LFS, and a fresh clone can leave nested
files as pointer text even when the top-level config looks fine. Detect a
pointer with:

```bash
head -n 1 "<path>"
```

A first line of `version https://git-lfs.github.com/spec/v1` means the real file
is missing. The files that must be real are `config.yaml`,
`train/pytorch_config.yaml`, `test/pose_cfg.yaml`, the
`training-datasets/.../metadata.yaml`, and the `snapshot-*.pt` checkpoints.

Materialize just this project:

```bash
git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"
```

Never hand-edit the scientific project files to work around a pointer.

## Required environment variables

```bash
export BIOMAP_REPO="/path/to/teaching-ai-to-read-mouse-behavior"
export BIOMAP_VIDEO_DIR="$BIOMAP_REPO/videos"
export BIOMAP_DLC_ENV="biomap-dlc"
export BIOMAP_DLC_DEVICE="cpu"
```

`BIOMAP_DLC_DEVICE` is passed directly to DeepLabCut; the runner never
auto-selects CUDA or MPS. `cpu` is the validated Mac path, because the
checkpoints were serialized on CUDA.

**Exports are per-terminal.** They apply only to the shell that ran them and to
processes it starts. A second Terminal window does not inherit them, so start
n8n from the shell where you set them, and re-export `BIOMAP_REPO` in any new
terminal you use for monitoring.

## Start n8n

From the repository root:

```bash
./n8n/setup/start_n8n_macos.sh
```

This is a **launcher, not a dependency installer**. It derives or preserves
`BIOMAP_REPO` and `BIOMAP_VIDEO_DIR`, sets or preserves `BIOMAP_DLC_ENV` and
`BIOMAP_DLC_DEVICE`, configures n8n environment access, and starts the local
n8n server. It does not install Git, Git LFS, Miniforge/Conda, Node.js, n8n,
DeepLabCut, or PyTorch, and it never creates the `biomap-dlc` environment.

Values you already exported take precedence. Keep the terminal open for the
whole job.

## Import the workflow

In the local n8n editor choose **Import from File** and select:

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

```bash
tail -n 0 -f "$BIOMAP_REPO/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

`-f` follows new output; `-n 0` suppresses lines that were already in the file.
Without `-n 0`, a finished progress bar from a previous run appears instantly
and is easily mistaken for a live job.

If you are in the repository root and have not exported `BIOMAP_REPO` in this
terminal:

```bash
tail -n 0 -f "$PWD/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Expected output:

```text
[n8n] DeepLabCut command started
[DLC Paw] START
[Python] DeepLabCut imported
[DLC Paw] Running pose prediction with batch size 8
[DLC Paw] 47/116451
```

Confirm a run is live by watching the counter advance, not by the presence of a
progress bar.

## Verify a video before blaming DeepLabCut

AVI input is already validated in this project, so a failure points at the
specific file rather than at format support:

```bash
conda run --no-capture-output -n biomap-dlc python - <<'PY'
import cv2
video = "/path/to/video.avi"
cap = cv2.VideoCapture(video)
print("opened:", cap.isOpened())
print("frames:", int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
print("fps:", cap.get(cv2.CAP_PROP_FPS))
ok, _ = cap.read()
print("first frame readable:", ok)
cap.release()
PY
```

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `ArgumentError: Argument --name requires a value` | `BIOMAP_DLC_ENV` is empty. Export it, restart n8n. |
| `Attempting to deserialize object on a CUDA device...` | Export `BIOMAP_DLC_DEVICE=cpu`. MPS fallback alone does not fix this. |
| A model or metadata file starts with a Git LFS URL | Run the scoped `git lfs pull`, then re-check every required file. |
| The live log stays blank | Check the execution is running, the command still ends with `2>&1 \| tee`, the log directory is writable, and n8n inherited all four variables. |
| `tail: /n8n/...: No such file or directory` | `BIOMAP_REPO` is unset in this terminal. Export it again or use `$PWD`. |
| Old progress appears before you start a run | Leftover log content. Watch with `tail -n 0 -f`. |
| `conda` not found by n8n | Start n8n from a shell where `conda --version` succeeds. |

Detailed explanations for each of these are in
[docs/BIOMAP_N8N_SETUP.md](docs/BIOMAP_N8N_SETUP.md#13-troubleshooting).
