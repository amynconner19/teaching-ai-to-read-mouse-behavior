# Teaching AI to Read Mouse Behavior

> **BrainHack Project:** Transform the current manual BIOMAP workflow into an open-source, automated, end-to-end behavioral analysis pipeline that processes batches of mouse behavioral videos from raw video to publication-ready results.

---

# TL;DR

The **Behavioral Inventory of Mouse Affective Pain (BIOMAP)** is a machine learning–based behavioral assay developed in the Wood Lab that combines computer vision, pose estimation, behavioral classification, and custom analyses to quantify pain-related behavior in freely moving mice.

The current BIOMAP workflow spans multiple software packages—including **DeepLabCut**, **SimBA**, and custom analysis scripts—and requires substantial manual interaction.

The goal of this BrainHack project is to begin transforming that workflow into a reproducible, automated, open-source pipeline capable of processing batches of behavioral videos with minimal user intervention.

Along the way, participants will also explore improved behavioral classification methods for distinguishing pain-related immobility from sleep, rest, and other inactive behavioral states.

---

# Project Resources

## Background

- [BIOMAP bioRxiv Preprint](paper/BIOMAP_Biorxiv.pdf)

## Workflow Documentation

- [Current BIOMAP Workflow](docs/CURRENT_WORKFLOW.md)
- [Desired BIOMAP Workflow](docs/DESIRED_WORKFLOW.md)

## Software

- [Software Overview](docs/software/README.md)
- [Install DeepLabCut](docs/software/INSTALL_DEEPLABCUT.md)
- [Install SimBA](docs/software/INSTALL_SIMBA.md)

## Data

- [Raw Video Directory](data/raw/README.md)

---

# Why this Matters

Current behavioral analysis pipelines often require researchers to manually transition between multiple software packages, repeatedly export and import intermediate files, and perform numerous GUI-based operations.

By transforming BIOMAP into an automated, reproducible workflow, we hope to:

- Reduce manual data processing
- Improve reproducibility across researchers and laboratories
- Standardize behavioral analyses
- Simplify onboarding for new users
- Enable larger-scale behavioral studies
- Accelerate scientific discovery

Although BIOMAP was originally developed to quantify sound-evoked pain, the resulting software could support research in pain, behavior, neurodegeneration, movement disorders, drug discovery, and other fields that rely on automated behavioral phenotyping.

---

# BrainHack Objectives

## Objective 1: Build an Automated End-to-End BIOMAP Pipeline

Develop an open, reproducible workflow capable of processing an entire batch of behavioral videos with minimal user interaction.

The long-term vision is a single command such as

```bash
biomap analyze data/raw_videos/
```

that automatically:

- Validates input videos and metadata
- Runs DeepLabCut pose estimation
- Performs tracking quality-control checks
- Runs SimBA feature extraction and behavioral classification
- Calculates BIOMAP behavioral features and pain-related metrics
- Generates standardized figures and reports
- Produces reproducible output files

BrainHack participants will contribute individual components toward this larger pipeline.

---

## Objective 2: Improve Behavioral-State Classification

Current BIOMAP analysis assumes reduced movement may indicate pain. However, mice may also be:

- Sleeping
- Resting
- Quietly awake
- Engaging in other low-movement behaviors

Participants will explore approaches for distinguishing these behavioral states using:

- Pose-estimation data
- Postural features
- Velocity and acceleration
- Temporal information
- Facial features
- Machine-learning methods
- Rule-based approaches

The goal is to establish useful baseline methods, identify promising features, and define future directions for behavioral-state classification.

A fully validated classifier is **not expected** during the BrainHack weekend.

---

# Current BIOMAP Workflow

BIOMAP currently combines:

- **DeepLabCut** for markerless pose estimation
- **SimBA** for behavioral feature extraction and supervised behavioral classification
- **Custom BIOMAP analysis scripts** for feature extraction, pain metrics, visualization, and statistical analysis

The current workflow requires repeated manual interaction and transitions between multiple independent software packages.

One major goal of this BrainHack project is to automate these transitions and reduce the workflow to a single reproducible pipeline.

For additional details, see:

- [Current BIOMAP Workflow](docs/CURRENT_WORKFLOW.md)
- [Desired BIOMAP Workflow](docs/DESIRED_WORKFLOW.md)

---

# Contributor Tracks

Participants are encouraged to contribute wherever their interests and expertise align.

| Track | Example Tasks | Helpful Skills |
|---------|---------------|----------------|
| **Pipeline Engineering** | Connect DeepLabCut, SimBA, and BIOMAP into a unified workflow | Python, software engineering |
| **DeepLabCut Integration** | Automate pose estimation and tracking workflows | DeepLabCut, computer vision |
| **SimBA Integration** | Automate feature extraction and behavioral classification | SimBA, behavioral analysis |
| **Behavioral Classification** | Improve classification of pain-related immobility versus other inactive states | Machine learning, statistics, time-series analysis |
| **Visualization & Reporting** | Generate publication-quality figures and standardized reports | pandas, matplotlib, Plotly |
| **Validation & Quality Control** | Build testing, quality-control tools, and reproducibility checks | Statistics, software testing |
| **Documentation & User Experience** | Improve installation guides, tutorials, workflow diagrams, onboarding materials, and troubleshooting | Technical writing, GitHub, Markdown |

Participants **do not need experience in every area.** We welcome contributors from neuroscience, computer science, data science, engineering, and related disciplines.

---

# Expected BrainHack Deliverables

The goal is **not** to complete the entire pipeline in one weekend.

Instead, we hope to make meaningful progress by producing:

- New automation tools
- Pipeline components
- Improved behavioral classification methods
- Standardized workflows
- Documentation and onboarding materials
- Quality-control tools
- Data visualization improvements
- Clearly defined future development priorities

Every contribution—whether code, documentation, testing, visualization, or scientific insight—helps move BIOMAP toward a fully automated behavioral analysis platform.

---

# Long-Term Vision

Ultimately, BIOMAP should allow researchers to analyze an entire behavioral experiment with a single command:

```bash
biomap analyze data/raw_videos/
```

The software would then automatically:

- Validate input videos
- Run DeepLabCut pose estimation
- Perform tracking quality control
- Run SimBA behavioral classification
- Calculate BIOMAP behavioral features
- Compute pain-related metrics
- Generate standardized figures
- Perform statistical analyses
- Create publication-ready reports
- Save all outputs in a reproducible directory structure

allowing researchers to focus on **scientific interpretation rather than manual data processing**.

---

# Getting Started

1. Read the [BIOMAP bioRxiv Preprint](paper/BIOMAP_Biorxiv.pdf).
2. Read the [Current BIOMAP Workflow](docs/CURRENT_WORKFLOW.md).
3. Read the [Desired BIOMAP Workflow](docs/DESIRED_WORKFLOW.md).
4. Install the required software:
   - [Software Overview](docs/software/README.md)
   - [Install DeepLabCut](docs/software/INSTALL_DEEPLABCUT.md)
   - [Install SimBA](docs/software/INSTALL_SIMBA.md)
5. Review the [Raw Video Directory](data/raw/README.md) to understand the expected input data structure.
6. Browse the GitHub Issues and choose a task that matches your interests.
7. Create a branch, make your changes, and submit a pull request.

We welcome contributors with backgrounds in neuroscience, computer science, software engineering, machine learning, data science, visualization, and technical writing.

---

# Acknowledgment

BrainHack is designed to foster **open, collaborative scientific software development**. Contributions will be tracked through GitHub issues, pull requests, commit history, and project discussions.

Meaningful contributions will be acknowledged appropriately in future software releases, presentations, preprints, and publications in accordance with standard scientific authorship and contribution practices.
