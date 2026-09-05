# Automated DeepLabCut Workflow

This Snakemake workflow runs every video through both pretrained BIOMAP
DeepLabCut models without opening the DeepLabCut GUI.

## Inputs

Place `.avi`, `.mp4`, or `.mov` files in:

```text
data/raw_videos/
```

The default model configurations are:

- `BIOMAP-Megan_G_-2026-03-17` for the nose tip and facial landmarks
- `BIOMAP Paw Digits-Megan G-2026-06-10` for paws and body landmarks

The wrapper creates a temporary portable copy of each DeepLabCut config. It
updates the original Windows `project_path` automatically and never edits the
trained project itself.

## Run on an Apple-silicon Mac

The default configuration forces CPU analysis to avoid the current
`torch.mps.current_device` error:

```bash
conda activate snakemake
snakemake --use-conda --cores 1
```

## Run with an NVIDIA GPU

```bash
snakemake \
  --use-conda \
  --cores 1 \
  --configfile config/config_windows_gpu.yaml
```

`--cores 1` intentionally runs one model job at a time and avoids loading both
networks into memory simultaneously.

## Preview without processing videos

```bash
snakemake --dry-run --use-conda --cores 1
```

## Outputs

Each input video produces two predictably named CSV files:

```text
results/deeplabcut/
├── nose/<video-name>.csv
├── paw_digits/<video-name>.csv
└── logs/<model>/<video-name>.log
```

These retain DeepLabCut's multi-row column headers and can be used by the
downstream BIOMAP merge and SimBA preparation steps.

## Git LFS model download

The trained snapshots are stored with Git LFS. If the wrapper reports that a
model file is still an LFS pointer, download both model directories with:

```bash
git lfs pull --include="deeplabcut-models/BIOMAP-Megan_G_-2026-03-17/**,deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"
```
