# Current BIOMAP Workflow

## Overview

The current BIOMAP workflow combines multiple software packages and custom analysis scripts to quantify pain-related behavior from behavioral videos.

While the workflow is functional, it requires numerous manual steps, transitions between independent software packages, and repeated user interaction.

The goal of this document is to describe the current workflow and identify opportunities for automation.

---

# Current Workflow

```text
Behavioral Video
        │
        ▼
DeepLabCut
    • Create/Open Project
    • Import Videos
    • Extract Frames
    • Label Frames
    • Train Network
    • Analyze Videos
    • Export Tracking CSV
        │
        ▼
Tracking CSV
        │
        ▼
SimBA
    • Create/Open Project
    • Import Videos
    • Import Tracking Data
    • Extract Features
    • Train Behavioral Classifiers (optional)
    • Run Machine Models
    • Export Behavioral Predictions
        │
        ▼
BIOMAP Analysis Scripts
    • Calculate Pain Metrics
    • Generate Figures
    • Perform Statistical Analysis
        │
        ▼
Final Results
