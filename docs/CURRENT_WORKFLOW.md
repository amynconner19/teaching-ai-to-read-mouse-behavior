# Current BIOMAP Workflow

## Overview

The current BIOMAP workflow combines trained DeepLabCut models, SimBA, and custom Python analysis scripts to quantify pain-related behavior from behavioral videos.

While the workflow has successfully supported published research, it requires numerous manual steps, transitions between independent software packages, and repeated user interaction. Several downstream analyses, including composite score calculation, figure generation, and statistical analysis, are currently performed manually.

The purpose of this document is to describe the current workflow and identify opportunities for automation during BrainHack.

---

# Current Workflow

```text
                     Batch of Behavioral Videos
                                │
                                ▼
              Run trained DeepLabCut models
      (Primary facial/body model + Paw tracking model)
                                │
                                ▼
                 Generate tracking CSV files
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
      BIOMAP Analysis Script                SimBA
     ("Sound Assay Analysis")        Behavioral Classification
                │                               │
                ▼                               ▼
 Calculate individual facial &         Calculate complex
 body-position measurements          behavioral metrics
 (Ear Ratio, Eye Ratio, etc.)      (Grooming, Rearing,
                │                  Pausing, Respiration)
                ▼
 Calculate percent change from
 baseline for each sound level
                │
                ▼
 Manual post-processing
 • Nose-tip crossing correction
                │
                ▼
 Manual composite score calculation
 • Facial Grimace Score
 • Body Position Score
                │
                ▼               
      Manual Figure Generation 
                │
                ▼
    Manual Statistical Analysis
                │
                ▼
             Final Results
```

---

# Current Manual Steps

The following steps currently require manual user interaction:

| Step | Current Method |
|------|----------------|
| Run trained DeepLabCut models | GUI |
| Export tracking CSV files | GUI |
| Run BIOMAP analysis script | Python script with user-specified inputs (CSV path, frame ranges, output name) |
| Calculate percent change from baseline | Automated within BIOMAP analysis script |
| Correct nose-tip crossing measurements | Manual |
| Calculate Facial Grimace composite score | Manual |
| Calculate Body Position composite score | Manual |
| Run SimBA | GUI |
| Generate figures | Manual |
| Statistical analysis | Manual |

---

# Current Limitations

The current workflow:

- Requires running multiple software packages independently.
- Requires manual file management between analysis steps.
- Requires user-specified frame ranges for each experimental condition.
- Requires manual correction of nose-tip crossing measurements.
- Requires manual calculation of composite Facial Grimace and Body Position scores.
- Requires manual figure generation and statistical analysis. 
- Is difficult to reproduce consistently across researchers and laboratories.

These limitations motivate the development of an automated, reproducible BIOMAP analysis pipeline.
