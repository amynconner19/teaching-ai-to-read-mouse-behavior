# Running a Trained DeepLabCut Model

## Overview

This guide describes how BIOMAP currently uses an existing, pre-trained DeepLabCut model to perform pose estimation on behavioral videos.

This guide assumes 
- DeepLabCut has already been installed.
- The current BIOMAP trained network is saved and available.

---

# Current Workflow

## 1. Launch DeepLabCut

Open the DeepLabCut graphical interface.

---

## 2. Load the Existing Project

Open the BIOMAP project by selecting the project's

```
config.yaml
```

configuration file.

---

## 3. Select Behavioral Videos

Load one or more behavioral videos for analysis.

The current workflow processes videos in batches.

---

## 4. Run Pose Estimation

Execute the **Analyze Videos** workflow.

DeepLabCut will:

- load the trained model
- estimate body-part locations
- calculate likelihood scores
- save tracking results

---

## 5. Quality Control (Optional)

Generate labeled videos to visually inspect tracking quality.

This step helps identify tracking failures before downstream analysis.

---

## 6. Export Tracking Results

DeepLabCut automatically exports tracking files.

Current BIOMAP uses:

- CSV files
- H5 files

The CSV output serves as the primary input for the downstream SimBA workflow.

---

# Outputs

```
Behavioral Videos
        │
        ▼
DeepLabCut
        │
        ▼
Tracking CSV
Tracking H5
(Optional) Labeled Videos
```

---

# Future Direction

One objective of the BIOMAP BrainHack project is to automate this workflow so that DeepLabCut can be executed directly from the BIOMAP pipeline without requiring manual interaction with the graphical interface.
