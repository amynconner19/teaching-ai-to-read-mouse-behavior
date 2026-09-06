# BIOMAP DeepLabCut n8n setup

This guide takes a researcher on a new Mac from a fresh clone to a running
DeepLabCut job launched by self-hosted n8n.

## Scope of this workflow

The current workflow is deliberately small:

```text
Manual Trigger → Pipeline Inputs → Run DeepLabCut
```

It runs **the pretrained PawDigits DeepLabCut model only**.

It does **not** run:

- facial / nosetip DeepLabCut
- the DLC merge step
- SimBA preprocessing, feature extraction, or classification
- ROI or calibration prerequisite checks
- BIOMAP terminal-state routing (`BIOMAP_RESULT`, Success / Failure branches)

Those stages are intentionally out of scope here. Do not read this workflow as
full BIOMAP automation.

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

**Steps 2 through 5 are prerequisites.** `start_n8n_macos.sh` does not perform
them. See [What the startup script does and does not
do](#what-the-startup-script-does-and-does-not-do).

## 1. Clone the repository

```bash
git clone <repository-url>
cd teaching-ai-to-read-mouse-behavior
```

## 2-5. Install the prerequisites

Install each of these yourself, before running anything in `n8n/setup/`:

| Prerequisite | Purpose |
| --- | --- |
| Git and Git LFS | Fetch the repository and materialize the trained model files |
| Miniforge or Conda | Provide the `conda` executable used to enter the DLC environment |
| Node.js and n8n | Run the local n8n server and its Execute Command node |
| A `biomap-dlc` Conda environment | Supply DeepLabCut, PyTorch, and OpenCV |

Typical installs:

```bash
git lfs install
npm install --global n8n
```

The `biomap-dlc` environment must contain a DeepLabCut and PyTorch combination
compatible with the checked-in checkpoints. Creating or repairing that
environment is a scientific-setup task and is outside this integration.

### Verify the prerequisites

Run these before going further. None of them starts inference.

```bash
git lfs version
conda env list
conda run -n biomap-dlc python -c 'import deeplabcut; print(deeplabcut.__version__)'
n8n --version
```

Expected shape of the results:

- `git lfs version` prints a version such as `git-lfs/3.8.0`. "command not
  found" means step 2 is incomplete.
- `conda env list` includes a line for `biomap-dlc`. If it is absent, the
  workflow cannot enter the environment.
- The DeepLabCut import prints a version string. An `ImportError` means the
  environment exists but is not usable for inference.
- `n8n --version` prints the installed n8n version.

## 6. Materialize the Git LFS model files

The trained DeepLabCut project is stored through Git LFS. A fresh or partial
clone can leave files on disk as small **pointer text** rather than the real
content. Nested files can stay as pointers even when the top-level
`config.yaml` looks correct, so check each file rather than assuming.

### Detect a pointer file

```bash
head -n 1 "<path>"
```

If the first line is:

```text
version https://git-lfs.github.com/spec/v1
```

the real file is **not** materialized.

### Files that must be real

Relative to `deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/`:

```text
config.yaml
dlc-models-pytorch/iteration-0/BIOMAP Paw DigitsJun10-trainset95shuffle1/train/pytorch_config.yaml
dlc-models-pytorch/iteration-0/BIOMAP Paw DigitsJun10-trainset95shuffle1/test/pose_cfg.yaml
dlc-models-pytorch/iteration-0/BIOMAP Paw DigitsJun10-trainset95shuffle1/train/snapshot-*.pt
training-datasets/iteration-0/UnaugmentedDataSet_BIOMAP Paw DigitsJun10/metadata.yaml
```

Check them in one pass from the repository root:

```bash
PAW="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10"
find "$PAW" \( -name '*.yaml' -o -name '*.pt' \) -print0 \
  | xargs -0 -I{} sh -c 'head -c 45 "{}" | grep -q "git-lfs" && echo "POINTER: {}"'
```

Any line printed is still a pointer.

### Materialize them

A scoped pull for just the PawDigits project is enough for this workflow, and
is much smaller than a full pull:

```bash
git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"
```

Re-run the detection command afterwards to confirm nothing is left as a
pointer.

Do not edit the model configuration, the trained weights, or any project file
to work around a pointer. The runner never rewrites the checked-in project; it
builds a disposable mirror under the ignored
`n8n/biomap_pipeline/results/.work/` directory instead.

## 7. Provide and verify an AVI input

Place at least one input AVI in a local directory that n8n can read. Videos are
runtime data and must never be committed.

AVI input has already been validated in this project, through both OpenCV and a
real DeepLabCut CPU inference startup, so a failure here points at the specific
file or its permissions rather than at format support.

To check a video before blaming DeepLabCut:

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

`opened: True` and `first frame readable: True` mean the video is fine. The
development sample reports 116451 frames at about 74 fps; a full run over it
takes tens of minutes to hours on CPU.

## 8. Configure the environment and start n8n

### The four variables

```bash
export BIOMAP_REPO="/path/to/teaching-ai-to-read-mouse-behavior"
export BIOMAP_VIDEO_DIR="$BIOMAP_REPO/videos"
export BIOMAP_DLC_ENV="biomap-dlc"
export BIOMAP_DLC_DEVICE="cpu"
```

| Variable | Meaning |
| --- | --- |
| `BIOMAP_REPO` | Absolute path to the checkout; the command's working directory |
| `BIOMAP_VIDEO_DIR` | Directory scanned for input videos |
| `BIOMAP_DLC_ENV` | Conda environment entered with `conda run` |
| `BIOMAP_DLC_DEVICE` | Device passed straight to DeepLabCut; `cpu` on Mac |

Portable placeholders live in `n8n/setup/environment.example`.

### Exports are per-terminal

An `export` applies **only to the shell that ran it and to processes that shell
starts**. A second Terminal window, tab, or a new SSH session does not inherit
it.

That has two practical consequences:

- n8n only sees these variables if it was started from a shell where they were
  set. Starting n8n from a different window than the one where you exported
  them will not work.
- A monitoring terminal that has not exported `BIOMAP_REPO` cannot expand it,
  so `tail "$BIOMAP_REPO/..."` resolves to `/n8n/...` and fails. Export it
  again in that shell, or use `$PWD` from the repository root.

### What the startup script does and does not do

`n8n/setup/start_n8n_macos.sh` is a **launcher, not a dependency installer**.

It does:

- derive or preserve `BIOMAP_REPO` (defaults to the checkout containing the script)
- derive or preserve `BIOMAP_VIDEO_DIR` (defaults to `$BIOMAP_REPO/videos`)
- set or preserve `BIOMAP_DLC_ENV` (defaults to `biomap-dlc`)
- set or preserve `BIOMAP_DLC_DEVICE` (defaults to `cpu`)
- configure n8n environment access so the Execute Command node can read those
  variables
- change into the repository and start the local n8n server

It does **not** install any of:

```text
Git            Git LFS        Miniforge/Conda      Node.js
n8n            DeepLabCut     PyTorch
```

It also never creates the `biomap-dlc` environment, downloads model weights, or
materializes Git LFS files.

Values already exported in your shell win; the script only fills in what is
missing. So both of these are valid:

```bash
# Let the script derive everything
./n8n/setup/start_n8n_macos.sh

# Or override first, then start
export BIOMAP_VIDEO_DIR="/Volumes/data/biomap_videos"
./n8n/setup/start_n8n_macos.sh
```

Run it from the repository root and keep the terminal open for the whole job:

```bash
./n8n/setup/start_n8n_macos.sh
```

The script exits early with a clear message if `BIOMAP_REPO` does not exist or
if `n8n` is not on `PATH`.

## 9. Import the workflow

1. Open the local n8n editor, normally <http://localhost:5678>.
2. Choose **Import from File**.
3. Select `n8n/n8n_biomap_workflow.json`.
4. Save the workflow, named **BIOMAP DeepLabCut Runner**.

The JSON contains exactly three nodes:

```text
Manual Trigger → Pipeline Inputs → Run DeepLabCut
```

`Pipeline Inputs` exposes only `video_dir`, taken from `BIOMAP_VIDEO_DIR`.
There are no SimBA or state-routing nodes.

## 10. Execute the workflow

Click **Execute workflow**. The stored command is:

```bash
/bin/bash -lc '
set -o pipefail
: "${BIOMAP_REPO:?BIOMAP_REPO is required}"
: "${BIOMAP_VIDEO_DIR:?BIOMAP_VIDEO_DIR is required}"
: "${BIOMAP_DLC_ENV:?BIOMAP_DLC_ENV is required}"
: "${BIOMAP_DLC_DEVICE:?BIOMAP_DLC_DEVICE is required}"
cd "$BIOMAP_REPO" || exit 70
mkdir -p n8n/biomap_pipeline/results/logs || exit 71
PYTHONUNBUFFERED=1 BIOMAP_DLC_ENV="$BIOMAP_DLC_ENV" BIOMAP_DLC_DEVICE="$BIOMAP_DLC_DEVICE" \
  ./n8n/biomap_pipeline/biomap dlc "$BIOMAP_VIDEO_DIR" --resume 2>&1 \
  | tee n8n/biomap_pipeline/results/logs/dlc_live.log
'
```

The `biomap dlc` entry point runs PawDigits only. It builds the disposable
runtime project, then calls this API inside `BIOMAP_DLC_ENV`:

```python
deeplabcut.analyze_videos(
    config,
    [video],
    video_extensions=".avi",
    shuffle=1,
    trainingsetindex=0,
    save_as_csv=True,
    destfolder=prediction_directory,
    device=device,
)
```

The project's own snapshot, body parts, training fraction, and cropping remain
authoritative.

### Why CPU on a Mac

`BIOMAP_DLC_DEVICE=cpu` is the validated Mac path. The checkpoints were
serialized on a CUDA machine, and loading them on a machine without CUDA fails
unless the device is mapped explicitly:

```text
Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

`PYTORCH_ENABLE_MPS_FALLBACK=1` does **not** fix this. That variable only lets
individual unimplemented operators fall back from MPS to CPU during inference;
it has no effect on how a CUDA-serialized checkpoint is deserialized. Set the
device explicitly. The runner never auto-selects CUDA or MPS.

## 11. Monitor live progress

From a second terminal, use:

```bash
tail -n 0 -f "$BIOMAP_REPO/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Why this exact form:

- `-f` follows the file and prints new output as it is written.
- `-n 0` starts from the end, showing nothing that was already there.

Without `-n 0`, `tail` first replays the tail of the previous run. A finished
progress bar from an earlier job then appears instantly and looks exactly like
a live one, which makes a failed or not-yet-started run look healthy. Use
`-n 0` so that anything you see was produced after you started watching.

If you are already in the repository root and have not exported `BIOMAP_REPO`
in this terminal:

```bash
tail -n 0 -f "$PWD/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

If you prefer `$BIOMAP_REPO` in a new terminal, export it again there first:

```bash
export BIOMAP_REPO="/path/to/teaching-ai-to-read-mouse-behavior"
```

Expected output from a healthy run:

```text
[n8n] DeepLabCut command started
[DLC Paw] START
[Python] DeepLabCut imported
[DLC Paw] DeepLabCut <version>; device cpu
[DLC Paw] Analyzing videos with ...
[DLC Paw] Running pose prediction with batch size 8
[DLC Paw] 47/116451
```

The frame counter must keep advancing. Output is unbuffered through
`PYTHONUNBUFFERED=1`, `python -u`, and `conda run --no-capture-output`, and
stdout and stderr are combined and streamed through `tee`.

## 12. Resume behavior and outputs

The workflow always passes `--resume`. Per video:

- a verified Paw CSV is logged as `SKIP_CACHED` and reused
- missing output starts inference
- empty, partial, malformed, wrong-body-part, or wrong-frame-count output is
  rejected and inference starts again

Runtime locations, all ignored by Git:

```text
n8n/biomap_pipeline/results/logs/dlc_live.log
n8n/biomap_pipeline/results/.work/dlc/
n8n/biomap_pipeline/results/tracking/paw/
```

## 13. Troubleshooting

### `BIOMAP_DLC_ENV` is empty

Symptom:

```text
ArgumentError: Argument --name requires a value
```

`conda run -n` received nothing. Export the variable in the shell that starts
n8n, then restart n8n:

```bash
export BIOMAP_DLC_ENV="biomap-dlc"
```

The stored command also fails fast with `BIOMAP_DLC_ENV is required` when the
variable is missing entirely.

### CUDA checkpoint on a Mac

Symptom:

```text
Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

Export the device explicitly and restart n8n:

```bash
export BIOMAP_DLC_DEVICE="cpu"
```

MPS fallback alone does not resolve this. See [Why CPU on a
Mac](#why-cpu-on-a-mac).

### Git LFS pointer text in model or metadata files

Symptoms: a config or metadata file parses as a short string instead of a
mapping, DeepLabCut reports a missing shuffle or snapshot, or

```bash
head -n 1 "<path>"
```

prints `version https://git-lfs.github.com/spec/v1`.

Run the scoped pull from step 6, then re-check every file in the list. Do not
hand-edit the scientific project files, and do not stage locally materialized
model files as part of the n8n contribution.

### The live log is blank

Check in this order:

- the workflow execution is actually still running in the n8n UI
- the **Run DeepLabCut** command still ends with `2>&1 | tee ...`
- `n8n/biomap_pipeline/results/logs/` exists and is writable
- n8n inherited all four variables, meaning it was started from a shell where
  they were exported

### A new terminal cannot resolve `$BIOMAP_REPO`

Symptom:

```text
tail: /n8n/biomap_pipeline/results/logs/dlc_live.log: No such file or directory
```

The path starts at `/` because `BIOMAP_REPO` is empty in this shell. Exports do
not cross terminal windows. Either export it again here, or use `$PWD` from the
repository root:

```bash
tail -n 0 -f "$PWD/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

### Old progress appears the moment you start watching

If a progress bar or completed run shows up instantly, before you clicked
**Execute workflow**, you are looking at leftover content from a previous run.
`dlc_live.log` is truncated by `tee` when a new run starts, but a plain
`tail -f` prints the existing tail first.

Watch with:

```bash
tail -n 0 -f "$BIOMAP_REPO/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Then everything on screen was written after you started watching. To confirm a
run is genuinely live, look for the counter advancing rather than for the mere
presence of a progress bar.

### Conda is unavailable to n8n

The workflow does not require you to activate `biomap-dlc`, but the `conda`
executable must be on the `PATH` of the process that runs the command. Start
n8n from a shell where this succeeds:

```bash
conda --version
```

If `conda` works in your interactive shell but not under n8n, the shell that
launched n8n did not load your Conda initialization. Start n8n from a normal
login shell in which `conda --version` works.

## 14. Lightweight validation

None of these run DeepLabCut inference:

```bash
bash -n n8n/setup/start_n8n_macos.sh
python -m json.tool n8n/n8n_biomap_workflow.json >/dev/null
git diff --check -- n8n/
```

The Python test suite lives in `n8n/biomap_pipeline/tests/`:

```bash
cd n8n/biomap_pipeline
python -m unittest discover -s tests -v
```
