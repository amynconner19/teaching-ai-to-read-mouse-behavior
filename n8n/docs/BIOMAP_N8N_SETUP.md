# BIOMAP n8n setup on macOS

This integration is intended for self-hosted n8n. A full BIOMAP run starts with
DeepLabCut and can remain active for tens of minutes depending on the input videos and
available GPU, so run n8n on a machine that has persistent access to the repository,
videos, Conda environments, trained models, and output directories.

n8n is only the orchestration layer. The workflow launches the repository's BIOMAP
CLI; scientific calculations remain in BIOMAP, DeepLabCut, and SimBA.

## Workflow

The checked-in workflow follows this path:

```text
Manual Trigger
→ Edit Fields / Pipeline Inputs
→ Run BIOMAP Pipeline
→ If
   ├─→ Success
   └─→ Failure
```

`Run BIOMAP Pipeline` stores this command:

```bash
/bin/bash -lc '
set -o pipefail
cd "$BIOMAP_REPO"
mkdir -p results/logs
./biomap analyze "$BIOMAP_VIDEO_DIR" 2>&1 | tee results/logs/biomap_live.log
'
```

This is the real, full pipeline command. It deliberately has no `--demo` flag and no
`--resume` flag. DeepLabCut is the first scientific stage and runs before the later
BIOMAP and SimBA stages.

`set -o pipefail` preserves a non-zero status from `./biomap analyze` even though its
combined stdout and stderr are piped through `tee`. The Execute Command node is set to
continue through its regular output on error, allowing the `If` node to route a failed
run to `Failure` instead of terminating the workflow at the command node.

## Required environment variables

The n8n process must receive all four variables:

```text
BIOMAP_REPO       Absolute path to the repository checkout
BIOMAP_VIDEO_DIR  Absolute path to the input video directory
BIOMAP_DLC_ENV    Conda environment used by DeepLabCut
BIOMAP_SIMBA_ENV  Conda environment used by SimBA
```

Portable example values are provided in `n8n/setup/environment.example`:

```bash
BIOMAP_REPO=/path/to/teaching-ai-to-read-mouse-behavior
BIOMAP_VIDEO_DIR=/path/to/teaching-ai-to-read-mouse-behavior/videos
BIOMAP_DLC_ENV=biomap-dlc
BIOMAP_SIMBA_ENV=biomap-simba
```

The example also enables workflow-node access to environment variables and the
Execute Command node. Do not replace the placeholders in the checked-in example with
personal paths.

## Prerequisites

Install a supported Node.js release and self-hosted n8n, then verify both commands:

```bash
node --version
npm install --global n8n
n8n --version
```

The repository-local launcher and both existing scientific Conda environments must
also be available:

```bash
./biomap --help
conda run -n biomap-dlc python --version
conda run -n biomap-simba python --version
```

Use the environment names configured in `BIOMAP_DLC_ENV` and
`BIOMAP_SIMBA_ENV` if they differ from these defaults. Environment creation,
scientific dependency installation, and trained-model management are outside n8n.

## Start n8n locally

From the repository root, run:

```bash
./n8n/setup/start_n8n_macos.sh
```

The helper calculates a portable repository path from its own location, defaults the
video directory to `$BIOMAP_REPO/videos`, defaults the Conda environment names to
`biomap-dlc` and `biomap-simba`, and exports the settings needed by self-hosted n8n.
Values already exported in the shell take precedence, for example:

```bash
export BIOMAP_REPO=/path/to/teaching-ai-to-read-mouse-behavior
export BIOMAP_VIDEO_DIR=/data/biomap/videos
export BIOMAP_DLC_ENV=biomap-dlc
export BIOMAP_SIMBA_ENV=biomap-simba
./n8n/setup/start_n8n_macos.sh
```

Keep that terminal open for the duration of long DeepLabCut jobs.

## Import and execute the workflow

1. Open the local n8n editor URL, normally `http://localhost:5678`.
2. Choose **Import from File** from the workflow menu.
3. Select `n8n/n8n_biomap_workflow.json`.
4. Confirm that the imported flow contains Manual Trigger, Edit Fields / Pipeline
   Inputs, Run BIOMAP Pipeline, If, Success, and Failure.
5. Select **Test workflow** (or execute the Manual Trigger) to start the full run.

The run begins DeepLabCut processing. Depending on GPU performance and video length,
this can take tens of minutes. There is no `--demo` flag in this production command.

## Logs and live progress

The command writes combined stdout and stderr to:

```text
results/logs/biomap_live.log
```

Monitor progress from another terminal with:

```bash
tail -f "$BIOMAP_REPO/results/logs/biomap_live.log"
```

The same output remains available in the n8n execution data. Because the node uses
`pipefail`, a BIOMAP error cannot be hidden by a successful `tee` process.

## Troubleshooting

### Environment variables are unavailable in the workflow

Start n8n through `n8n/setup/start_n8n_macos.sh`, or export all four required BIOMAP
variables before running `n8n start`. The helper also exports:

```bash
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
NODES_EXCLUDE=[]
```

These settings allow the checked-in workflow to read its environment and use Execute
Command in the self-hosted runtime.

### The workflow reaches Failure

Inspect the n8n execution output and the live log:

```bash
tail -f "$BIOMAP_REPO/results/logs/biomap_live.log"
```

The Failure path means the command did not produce a zero exit code (or no exit code
was available). Resolve the underlying CLI, environment, input, model, or filesystem
error and execute the workflow again.

### DeepLabCut appears idle

DeepLabCut is the first scientific stage and may take tens of minutes. Check the live
log and GPU activity before concluding that it has stopped. Do not add `--demo` to the
full-run workflow merely to bypass this stage.

### `n8n`, `conda`, or `./biomap` is unavailable

Run n8n under the same macOS account and shell environment that can execute the CLI
and both Conda environments. Verify each command from the repository root before
starting n8n. Keep scientific setup and calculations in the BIOMAP codebase rather
than adding them to workflow nodes.
