# BIOMAP n8n setup on macOS

This guide installs n8n directly on macOS and connects it to the existing BIOMAP
command-line pipeline. n8n is only the automation and orchestration layer; it does not
contain or replace any scientific calculations.

The integration requires the pipeline implementation and its `biomap analyze` CLI to
already be available in the repository checkout. The n8n files do not install or
implement that CLI, DeepLabCut analysis, SimBA inference, feature calculations, or
report generation.

## Fresh machine / first-time setup

Follow these steps on a Mac that has not previously run n8n.

1. Clone the repository and enter the checkout:

   ```bash
   git clone <repository-url>
   cd teaching-ai-to-read-mouse-behavior
   ```

2. Install Node.js 24 using the macOS installer from the Node.js website or a Node
   version manager. Confirm that Node 24 and npm are available:

   ```bash
   node --version
   npm --version
   ```

3. Install n8n globally with npm and verify the command:

   ```bash
   npm install --global n8n
   n8n --version
   ```

4. Install the Apple Silicon Miniforge distribution, initialize Conda for the shell,
   and open a new terminal. Confirm that Conda is available:

   ```bash
   conda --version
   ```

5. Verify that the two pipeline environments already exist and are runnable:

   ```bash
   conda env list
   conda run -n biomap-dlc python --version
   conda run -n biomap-simba python --version
   ```

   Their required names are `biomap-dlc` and `biomap-simba`. Environment creation and
   scientific dependency installation belong to the BIOMAP pipeline implementation,
   not to n8n.

6. Verify that this checkout includes the pipeline CLI:

   ```bash
   ./biomap --help
   ./biomap analyze --help
   ```

   If `./biomap` is absent, obtain or merge the BIOMAP pipeline implementation before
   continuing. This n8n integration cannot run independently of that implementation.

7. Start n8n with the repository helper:

   ```bash
   ./n8n/setup/start_n8n_macos.sh
   ```

8. Open [http://localhost:5678](http://localhost:5678) in a browser.

9. In the n8n workflow menu, choose **Import from File** and select:

   ```text
   n8n/n8n_biomap_workflow.json
   ```

10. Open **Run BIOMAP Pipeline**, confirm its input directory and flags, save the
    workflow, and run it from the Manual Trigger.

For a safe first check, temporarily use `./biomap analyze videos/ --dry-run` in the
Execute Command node. It validates the orchestration command without starting
DeepLabCut or SimBA inference.

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

## Troubleshooting

### `n8n: command not found`

Confirm that the global npm installation succeeded:

```bash
npm install --global n8n
npm prefix --global
```

The global npm `bin` directory must be on `PATH`. Open a new terminal after installing
n8n, then rerun `n8n --version`. If Node was installed with a version manager, activate
Node 24 in the same shell before starting n8n.

### `conda: command not found`

Confirm Miniforge is installed and initialize it for the default macOS shell:

```bash
"$HOME/miniforge3/bin/conda" init zsh
```

Close and reopen the terminal, then run `conda --version`. If Miniforge was installed
somewhere else, substitute that installation path.

### `biomap: command not found`

The supplied workflow uses the repository-local `./biomap` launcher, not a scientific
implementation supplied by n8n. From the repository root, check:

```bash
test -x ./biomap
./biomap analyze --help
```

If the file is missing, obtain or merge the BIOMAP pipeline implementation. If the file
exists but is not executable, correct its executable permission in the pipeline
implementation rather than replacing it with logic inside the n8n workflow.

### Missing `biomap-dlc` or `biomap-simba`

List and probe the environments:

```bash
conda env list
conda run -n biomap-dlc python --version
conda run -n biomap-simba python --version
```

Create the missing environment using the validated environment definition supplied by
the BIOMAP pipeline implementation. Keep the exact names because the orchestration CLI
uses them. Do not install scientific packages ad hoc from the n8n workflow.

### `localhost:5678` is not opening

Keep the terminal running `start_n8n_macos.sh` open and inspect it for startup errors.
Confirm that n8n is listening on the expected port:

```bash
lsof -nP -iTCP:5678 -sTCP:LISTEN
```

If nothing is listening, resolve the terminal error and restart the helper. If another
process owns port 5678, stop that service or configure n8n to use an available port,
then open the corresponding localhost URL. Also confirm that the URL uses `http`, not
`https`.
