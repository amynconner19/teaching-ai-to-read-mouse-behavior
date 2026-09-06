# BIOMAP DeepLabCut n8n setup

This guide takes a new researcher from a clone to the simplified, self-hosted
n8n workflow:

```text
Manual Trigger → Pipeline Inputs → Run DeepLabCut
```

The current workflow runs only the pretrained PawDigits DeepLabCut model. It
does not run facial tracking, merge DLC files, start SimBA, or route BIOMAP
terminal states.

## 1. Clone and materialize model files

```bash
git clone <repository-url>
cd teaching-ai-to-read-mouse-behavior
git lfs install
git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"
```

The required scientific configuration is:

```text
deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml
```

Do not edit the model configuration, trained weights, or project files for the
n8n integration. The runner creates an ignored runtime mirror instead.

To detect an unmaterialized LFS pointer:

```bash
head -n 1 "deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml"
```

`version https://git-lfs.github.com/spec/v1` means the real file is not present.

## 2. Install local prerequisites

Install:

- Conda or Miniforge
- a working `biomap-dlc` environment containing the repository-compatible
  DeepLabCut and PyTorch versions
- Node.js and self-hosted n8n

Example n8n installation:

```bash
npm install --global n8n
n8n --version
```

Confirm the DLC environment without running inference:

```bash
conda env list
conda run -n biomap-dlc python -c 'import deeplabcut; print(deeplabcut.__version__)'
```

The workflow does not assume the shell or n8n process is already activated in
`biomap-dlc`. The DLC subprocess enters it through `conda run`.

## 3. Provide an AVI input

Place or mount the input AVI in a local directory readable by n8n. Videos are
runtime data and must not be committed.

AVI input has been validated through OpenCV and real DeepLabCut CPU inference
startup. The sample development video contained 116451 frames; a full run can
take tens of minutes.

## 4. Configure the environment

Set these variables in the same shell that starts n8n:

```bash
export BIOMAP_REPO="/path/to/teaching-ai-to-read-mouse-behavior"
export BIOMAP_VIDEO_DIR="$BIOMAP_REPO/videos"
export BIOMAP_DLC_ENV="biomap-dlc"
export BIOMAP_DLC_DEVICE="cpu"
```

Portable placeholders are also provided in `n8n/setup/environment.example`.
The supplied startup helper preserves values already set in the environment;
otherwise it derives `BIOMAP_REPO` and `BIOMAP_VIDEO_DIR` from its own location
and defaults the environment and device to `biomap-dlc` and `cpu`.

CPU is intentional for the validated Mac path. These checkpoints were saved on
CUDA, and an explicit `device="cpu"` prevents CUDA deserialization failures.
The code does not automatically choose CUDA or MPS.

## 5. Start self-hosted n8n

From the repository root:

```bash
./n8n/setup/start_n8n_macos.sh
```

The helper starts n8n with the repository as its working directory and enables
the Execute Command node and environment access. Keep this terminal open.

## 6. Import the workflow

1. Open the local n8n editor, normally <http://localhost:5678>.
2. Choose **Import from File**.
3. Select `n8n/n8n_biomap_workflow.json`.
4. Save **BIOMAP DeepLabCut Runner**.

The JSON contains exactly:

```text
Manual Trigger → Pipeline Inputs → Run DeepLabCut
```

`Pipeline Inputs` exposes only `video_dir`, derived from
`BIOMAP_VIDEO_DIR`. There are no stale SimBA or state-routing nodes.

## 7. Execute

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

The `biomap dlc` entry point runs only PawDigits. It builds a disposable runtime
project, then launches this API inside `BIOMAP_DLC_ENV`:

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

The model's existing snapshot, body parts, training fraction, cropping, and
other scientific settings remain authoritative.

## 8. Monitor progress

In another terminal:

```bash
tail -f "$BIOMAP_REPO/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Development-machine example only:

```bash
tail -f "/Users/jkathila/Desktop/work/teaching-ai-to-read-mouse-behavior/n8n/biomap_pipeline/results/logs/dlc_live.log"
```

Expected output includes:

```text
[n8n] DeepLabCut command started
[DLC Paw] START
[Python] DeepLabCut imported
[DLC Paw] DeepLabCut <version>; device cpu
[DLC Paw] Analyzing videos with ...
[DLC Paw] Running pose prediction with batch size 8
[DLC Paw] 47/116451
```

Output is unbuffered through `PYTHONUNBUFFERED=1`, `python -u`, and
`conda run --no-capture-output`. stdout and stderr are combined and streamed
through `tee`.

## 9. Resume behavior and outputs

The workflow always supplies `--resume`. For each video:

- a verified Paw CSV is logged as `SKIP_CACHED` and reused;
- missing output starts inference;
- an empty, partial, malformed, wrong-body-part, or wrong-frame-count CSV is
  rejected and inference starts again.

Runtime locations, all ignored by Git:

```text
n8n/biomap_pipeline/results/logs/dlc_live.log
n8n/biomap_pipeline/results/.work/dlc/
n8n/biomap_pipeline/results/tracking/paw/
```

## 10. Troubleshooting

### Empty DLC environment

Symptom:

```text
ArgumentError: Argument --name requires a value
```

Set `BIOMAP_DLC_ENV=biomap-dlc` before starting n8n. The supplied workflow
also checks for the variable and fails clearly when it is absent.

### CUDA checkpoint error on Mac

Symptom:

```text
Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

Set and export:

```bash
BIOMAP_DLC_DEVICE=cpu
```

MPS fallback does not solve CUDA checkpoint deserialization.

### Git LFS pointer text

If a required model file begins with the Git LFS URL, run the scoped
`git lfs pull` command from step 1. Do not stage the resulting local model-file
changes with the n8n PR.

### Blank live log

- Confirm the workflow execution is active.
- Confirm `Run DeepLabCut` still contains `2>&1 | tee`.
- Confirm `n8n/biomap_pipeline/results/logs/` is writable.
- Confirm n8n inherited all four required environment variables.

### Conda is unavailable to n8n

Start n8n from a shell where `conda --version` succeeds. The workflow does not
require manual activation of `biomap-dlc`, but the `conda` executable must be on
`PATH`.

## 11. Lightweight validation

These checks do not run DeepLabCut inference:

```bash
cd n8n/biomap_pipeline
python -m unittest discover -s tests -v
python -m json.tool ../n8n_biomap_workflow.json >/dev/null
cd ../..
git diff --check -- n8n/
```
