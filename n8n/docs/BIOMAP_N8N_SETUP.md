# BIOMAP n8n setup on macOS

This guide installs n8n directly on macOS and connects it to the existing BIOMAP
command-line pipeline. n8n is only the automation and orchestration layer; it does not
contain or replace any scientific calculations.

## Prerequisites

### Node.js 24 and n8n

This setup uses Node.js 24. Confirm that Node and npm are available:

```bash
node --version
npm --version
```

Install n8n globally with npm:

```bash
npm install --global n8n
n8n --version
```

### Miniforge and Conda environments

Install Miniforge for the native macOS architecture and initialize Conda for the shell.
The BIOMAP wrappers expect these existing environment names:

```text
biomap-dlc
biomap-simba
```

Confirm both environments are visible before starting n8n:

```bash
conda env list
```

The environments contain the scientific dependencies. n8n should not install or
replace DeepLabCut, SimBA, model files, or their dependencies.

## Start n8n locally

From the repository root, run:

```bash
./n8n/setup/start_n8n_macos.sh
```

The helper derives the repository root from its own location, exports the BIOMAP Conda
environment names, enables environment access in workflow nodes, enables the Execute
Command node, and then runs `n8n start`.

For reference, `n8n/setup/environment.example` lists the variables without personal
paths. The startup helper sets them automatically for its n8n process.

Open the editor URL shown by n8n and import `n8n/n8n_biomap_workflow.json` using the
workflow menu's **Import from File** action.

## Execute Command usage

The supplied workflow has one scientific execution path:

```text
Manual Trigger → Run BIOMAP Pipeline
```

The Execute Command node changes to `BIOMAP_REPO` and invokes the repository-local CLI.
This keeps Conda activation and all pipeline stages in the BIOMAP orchestration code
rather than duplicating them in n8n.

Recommended production command:

```bash
./biomap analyze videos/ --resume
```

Hackathon/demo command using cached tracking outputs:

```bash
./biomap analyze videos/ --resume --demo
```

Safe validation command that prints commands and paths without executing the pipeline:

```bash
./biomap analyze videos/ --dry-run
```

To use a different input directory, replace `videos/` in the Execute Command node with
the desired path. Quote paths that contain spaces.

## Operational notes

- DeepLabCut inference can be long-running. Use `--resume` to reuse verified completed
  stages and `--demo` when suitable cached tracking outputs are available.
- SimBA requires the existing project ROI setup, including the scientifically defined
  `AboveFloor` ROI, before headless inference can complete.
- A non-zero CLI exit status makes the Execute Command node fail. The CLI output names
  the failed stage and expected output location.
- Run n8n under the same macOS user that can access the repository, Conda installation,
  input videos, models, and output directories.
- Replace the Manual Trigger with an appropriate file or external trigger later without
  expanding the scientific pipeline into separate n8n nodes.
