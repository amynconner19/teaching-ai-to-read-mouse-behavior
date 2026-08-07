# BIOMAP DeepLabCut Models

This directory contains the pretrained DeepLabCut (DLC) models used in the BIOMAP workflow.

BIOMAP uses two pretrained DeepLabCut projects for pose estimation. Both models have already been trained and should be used as provided.

**You do not need to create a new DeepLabCut project or train a new model.**

## Pretrained Models

### 1. BIOMAP Paw Digits

```text
BIOMAP Paw Digits-Megan G-2026-06-10/
```

This DeepLabCut project contains the pretrained model used to track paw, digit, and other body landmarks required for the BIOMAP workflow.

### 2. BIOMAP

```text
BIOMAP-Megan_G_-2026-03-17/
```

This directory contains the second pretrained DeepLabCut model used in the BIOMAP workflow.

## Downloading the Models

Clone or download the complete `teaching-ai-to-read-mouse-behavior` repository.

The pretrained DeepLabCut projects are located under:

```text
models/
```

Keep the contents and internal directory structure of each DeepLabCut project intact.

Do not rename or reorganize the files or directories within either project.

## Updating the DeepLabCut Project Paths

DeepLabCut stores the location of each project in its `config.yaml` file.

Because these projects were created on a different computer, you must update `project_path` before using each model.

### BIOMAP Paw Digits

Open:

```text
models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml
```

Change:

```yaml
project_path: C:\Users\lmbwo\Desktop\BIOMAP Paw Digits-Megan G-2026-06-10
```

to the location of this folder on your computer.

For example, on Windows:

```yaml
project_path: C:\Users\YourUsername\Desktop\teaching-ai-to-read-mouse-behavior\models\BIOMAP Paw Digits-Megan G-2026-06-10
```

or on macOS:

```yaml
project_path: /Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/models/BIOMAP Paw Digits-Megan G-2026-06-10
```

### BIOMAP

Open:

```text
models/BIOMAP-Megan_G_-2026-03-17/config.yaml
```

Similarly, update its `project_path` to the location of the `BIOMAP-Megan_G_-2026-03-17` folder on your computer.

Your exact paths will depend on where you cloned or downloaded the repository.

## Original Training Videos

The original videos used to train the DeepLabCut models are not included in this repository because of their large file sizes.

You may therefore see paths to the original training videos under `video_sets` in the DeepLabCut `config.yaml` files.

These paths do not need to be changed when using the pretrained models to analyze new videos.

**Do not replace the entries under `video_sets` with the videos you want to analyze.**

## Using the Models

For the BIOMAP workflow:

1. Install DeepLabCut according to the installation instructions provided in this repository.
2. Download or clone this repository.
3. Locate the pretrained projects in `models/`.
4. Update `project_path` in each project's `config.yaml`.
5. Use the existing `config.yaml` files and pretrained models to analyze the provided experimental videos.
6. Do not create new DeepLabCut projects.
7. Do not retrain the models.

The resulting DeepLabCut tracking data will be used in subsequent steps of the BIOMAP workflow.

## Important

Do not modify the internal DeepLabCut project structure.

Directories such as:

```text
dlc-models-pytorch/
training-datasets/
labeled-data/
evaluation-results-pytorch/
```

are part of the pretrained DeepLabCut projects and should remain in their original locations.
