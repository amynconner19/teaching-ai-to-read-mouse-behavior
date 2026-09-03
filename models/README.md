# BIOMAP DeepLabCut Models

This directory contains two pretrained DeepLabCut (DLC) projects used in the BIOMAP workflow.

The models are already trained. No model creation or retraining is required.

## Example Video

[Download the example behavioral video from Google Drive](https://drive.google.com/file/d/1w2l9ZiiBPIbYl2EyvN27BHWj-Yq1zH_2/view?usp=drive_link)

After downloading the video, copy it into the `videos/` folder of **both** DeepLabCut projects:

```text
models/BIOMAP Paw Digits-Megan G-2026-06-10/videos/
models/BIOMAP-Megan_G_-2026-03-17/videos/
```

## Model 1 — BIOMAP Paw Digits

```text
models/BIOMAP Paw Digits-Megan G-2026-06-10/
```

This model tracks paw, digit, and other body landmarks used in the BIOMAP analysis.

Analyze the video located in:

```text
models/BIOMAP Paw Digits-Megan G-2026-06-10/videos/
```

## Model 2 — BIOMAP

```text
models/BIOMAP-Megan_G_-2026-03-17/
```

This is the second pose-estimation model used in the BIOMAP workflow.

Analyze the video located in:

```text
models/BIOMAP-Megan_G_-2026-03-17/videos/
```

## Setup

Clone or download the complete `teaching-ai-to-read-mouse-behavior` repository and keep the internal structure of both projects intact.

DeepLabCut stores the location of each project in its `config.yaml` file. Because these projects were created on another computer, update the `project_path` in each configuration file before running the models.

### BIOMAP Paw Digits

Open:

```text
models/BIOMAP Paw Digits-Megan G-2026-06-10/config.yaml
```

Change `project_path` to the location of this project folder on your computer.

Windows example:

```yaml
project_path: C:\Users\YourUsername\Desktop\teaching-ai-to-read-mouse-behavior\models\BIOMAP Paw Digits-Megan G-2026-06-10
```

macOS example:

```yaml
project_path: /Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/models/BIOMAP Paw Digits-Megan G-2026-06-10
```

### BIOMAP

Open:

```text
models/BIOMAP-Megan_G_-2026-03-17/config.yaml
```

Update `project_path` to the location of the `BIOMAP-Megan_G_-2026-03-17` folder on your computer.

## Analyze the Videos

For each project:

1. Open its existing `config.yaml` file in DeepLabCut.
2. Select **Analyze videos**.
3. Select the video inside that project’s `videos/` folder.
4. Run the pretrained model.
5. Keep the resulting tracking files in the project’s `videos/` folder for the next stage of the BIOMAP workflow.

Repeat these steps using both pretrained projects.

## About `video_sets`

The `video_sets` section of each `config.yaml` may contain paths to the original training videos. Those videos are not included because of their large file sizes.

These entries are part of the original project configuration and are not the videos being analyzed during this exercise. They can remain unchanged.

## Project Structure

Keep the model folders and their contents in their original locations, including:

```text
dlc-models-pytorch/
training-datasets/
labeled-data/
evaluation-results-pytorch/
videos/
```

The DeepLabCut tracking files generated from the provided videos will be used in subsequent BIOMAP analysis steps.
