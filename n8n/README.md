# BIOMAP n8n integration

This directory contains the orchestration layer that launches the repository's real
BIOMAP command-line pipeline. Scientific calculations remain in the BIOMAP, DeepLabCut,
and SimBA code—not in n8n.

```text
Manual Trigger
  → Edit Fields / Pipeline Inputs
  → Run BIOMAP Pipeline
  → If
      → Success
      → Failure
```

Self-hosted n8n is the intended runtime because DeepLabCut inference is a long-running,
local scientific job. Depending on the video and available GPU, DLC can take tens of
minutes. DeepLabCut is the first scientific stage in a full run.

## Production execution

`Run BIOMAP Pipeline` executes:

```bash
/bin/bash -lc '
set -o pipefail
cd "$BIOMAP_REPO"
mkdir -p results/logs
./biomap analyze "$BIOMAP_VIDEO_DIR" 2>&1 | tee results/logs/biomap_live.log
'
```

There is deliberately no `--demo` flag. `set -o pipefail` preserves a non-zero BIOMAP
exit status even though output is piped through `tee`. The node continues its error
item on the regular output so the downstream If node can select Success or Failure.

Monitor the live run from another terminal:

```bash
tail -f "$BIOMAP_REPO/results/logs/biomap_live.log"
```

## Required environment

The self-hosted n8n process must receive:

```text
BIOMAP_REPO
BIOMAP_VIDEO_DIR
BIOMAP_DLC_ENV
BIOMAP_SIMBA_ENV
```

Portable examples are provided in `setup/environment.example`. The macOS startup
helper supplies repository-relative defaults and respects values already exported by
the operator.

## Run locally

From the repository root:

```bash
./n8n/setup/start_n8n_macos.sh
```

Open the editor URL printed by n8n (normally `http://localhost:5678`), choose **Import
from File**, select `n8n/n8n_biomap_workflow.json`, save it, and click **Test workflow**.
The Manual Trigger starts the full pipeline.

See [BIOMAP_N8N_SETUP.md](docs/BIOMAP_N8N_SETUP.md) for installation, environment,
import, execution, monitoring, and troubleshooting details.
