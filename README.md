# Teaching AI to Read Mouse Behavior
### TL;DR

> **BrainHack Project:** Transform the current BIOMAP workflow into an open-source, automated, end-to-end behavioral analysis pipeline that processes batches of mouse behavioral videos—from raw videos to publication-ready figures and analysis-ready data.

---

# Overview

The **Behavioral Inventory of Mouse Affective Pain (BIOMAP)** is a machine learning–based behavioral assay developed in the Wood Lab that quantifies pain-related behavior in freely moving mice using computer vision, pose estimation, behavioral classification, and custom behavioral analyses.

The current BIOMAP workflow combines:

- Multiple trained DeepLabCut models
- SimBA behavioral classification
- Custom Python analysis scripts
- Manual calculations
- Manual figure generation
- Manual statistical analyses

While the workflow has successfully supported published research, many downstream analysis steps still require substantial user interaction.

The goal of this BrainHack project is to begin transforming this workflow into a reproducible, automated, and open-source software pipeline.

---

# Long-Term Vision

Ultimately, a researcher should be able to analyze an entire experiment using a single command.

```bash
biomap analyze data/raw_videos/
```

The software would automatically:

- Load a batch of behavioral videos
- Run all required trained DeepLabCut models
- Generate tracking data (CSV/H5 files)
- Run SimBA behavioral analyses
- Calculate baseline-normalized behavioral measurements (percent change from baseline) for each sound-level condition
- Apply automated post-processing (e.g., nose-tip crossing correction)
- Calculate Facial Grimace and Body Position composite scores
- Generate publication-quality figures for facial, body-position, and complex behavioral metrics
- Export statistical analysis-ready datasets

allowing researchers to focus on scientific interpretation rather than manual data processing.

---

# Why This Matters

Behavioral phenotyping often requires researchers to manually move between multiple software packages, repeatedly import and export intermediate files, perform manual calculations, and generate figures using several independent tools.

Automating the BIOMAP workflow will:

- Improve reproducibility
- Reduce manual processing time
- Standardize analyses across laboratories
- Simplify onboarding for new users
- Improve transparency
- Enable larger behavioral datasets
- Facilitate collaborative software development

Although BIOMAP was originally developed to study sound-evoked pain, the resulting software could support research in:

- Pain
- Neuroscience
- Neurodegeneration
- Movement disorders
- Drug discovery
- Automated behavioral phenotyping

---

# Current Workflow

Today's workflow consists of several independent analysis stages.

```text
Batch of Behavioral Videos
            │
            ▼
Run trained DeepLabCut models
            │
            ▼
Tracking CSV files
            │
            ├────────────────────────────┐
            │                            │
            ▼                            ▼
BIOMAP Analysis Script              SimBA
            │                            │
            ▼                            ▼
Facial & Body Metrics          Complex Behaviors
            │                            │
            └──────────────┬─────────────┘
                           ▼
                  Manual Calculations
                           ▼
                  Manual Figure Generation
                           ▼
                  Manual Statistics (Prism)
```

For a detailed description of the current workflow:

- [Current Workflow](docs/CURRENT_WORKFLOW.md)

---

# BrainHack Objectives

## Objective 1

### Build an Automated End-to-End BIOMAP Pipeline

Automate the existing workflow so that batches of behavioral videos can be processed with minimal user interaction.

Desired capabilities include:

- Running multiple trained DeepLabCut models automatically
- Executing the existing BIOMAP analysis scripts
- Running SimBA automatically
- Organizing intermediate files
- Calculating baseline-normalized behavioral metrics
- Automatically calculating composite scores
- Generating standardized figures
- Exporting analysis-ready tables

---

## Objective 2

### Improve Behavioral-State Classification

Current BIOMAP analyses quantify facial grimace, body position, and complex behaviors.

BrainHack participants may also explore methods for improving classification of inactive behavioral states, including:

- Pain-related immobility
- Sleep
- Rest
- Quiet wakefulness

Potential approaches include:

- Pose-estimation features
- Temporal information
- Machine learning
- Rule-based classification
- Additional behavioral features

A fully validated classifier is **not expected** during the BrainHack weekend.

---

# Project Resources

## Background

- [BIOMAP bioRxiv Preprint](paper/BIOMAP_Biorxiv.pdf)

## Documentation

- [Current Workflow](docs/CURRENT_WORKFLOW.md)
- [Desired Workflow](docs/DESIRED_WORKFLOW.md)
- [Pipeline Components](docs/PIPELINE_COMPONENTS.md)
- [Video Structure](docs/VIDEO_STRUCTURE.md)

## Software

- [Software Overview](docs/software/README.md)
- [Install DeepLabCut](docs/software/INSTALL_DEEPLABCUT.md)
- [Run DeepLabCut](docs/software/RUN_DEEPLABCUT.md)
- [Install SimBA](docs/software/INSTALL_SIMBA.md)
- [Run SimBA](docs/software/RUN_SIMBA.md)

## Data

- [Raw Video Directory](data/raw/README.md)

## Analysis

- [BIOMAP Analysis](docs/analysis/README.md)

---

# Contributor Tracks

Participants are encouraged to contribute wherever their interests and expertise align.

| Track | Example Tasks | Helpful Skills |
|---------|---------------|----------------|
| Pipeline Engineering | Connect existing software into a unified workflow | Python, software engineering |
| DeepLabCut Integration | Automate execution of trained DeepLabCut models | DeepLabCut, computer vision |
| SimBA Integration | Automate behavioral classification | SimBA, behavioral analysis |
| BIOMAP Analysis | Automate composite score calculations and baseline normalization | Python, data analysis |
| Figure Generation | Create publication-quality figures | matplotlib, Plotly |
| Quality Control | Build validation and QC reports | Statistics, software testing |
| Documentation | Improve onboarding, tutorials, diagrams, and troubleshooting | GitHub, Markdown |
| Experimental Design | Automate metadata handling, sound epochs, and baseline calculations | Neuroscience, data science |

Participants **do not need experience in every area.**

We welcome contributors from neuroscience, computer science, engineering, data science, machine learning, software engineering, and scientific visualization.

---

# Expected BrainHack Deliverables

The goal is **not** to complete the entire pipeline in one weekend.

Instead, we hope to make meaningful progress by:

- Automating portions of the existing workflow
- Connecting existing software packages
- Improving reproducibility
- Reducing manual calculations
- Automating figure generation
- Improving documentation
- Building quality-control tools
- Identifying future development priorities

Every contribution—whether code, documentation, testing, visualization, or scientific insight—helps move BIOMAP toward a fully automated behavioral analysis platform.

---

# Getting Started

If you're new to the project, we recommend the following order:

1. 📖 Read the [BIOMAP bioRxiv Preprint](paper/BIOMAP_Biorxiv.pdf) to understand the scientific motivation.
2. 🔬 Review the [Current Workflow](docs/CURRENT_WORKFLOW.md) to learn how BIOMAP is analyzed today.
3. 🚀 Explore the [Desired Workflow](docs/DESIRED_WORKFLOW.md) to see the long-term vision for the project.
4. 🗺️ Browse the [Pipeline Components](docs/PIPELINE_COMPONENTS.md) to identify areas for contribution.
5. 🎥 Review the [Experimental Video Structure](docs/VIDEO_STRUCTURE.md) to understand the behavioral assay.
6. 💻 Install the required software:
   - [Software Overview](docs/software/README.md)
   - [Install DeepLabCut](docs/software/INSTALL_DEEPLABCUT.md)
   - [Run DeepLabCut](docs/software/RUN_DEEPLABCUT.md)
   - [Install SimBA](docs/software/INSTALL_SIMBA.md)
   - [Run SimBA](docs/software/RUN_SIMBA.md)
7. 📝 Browse the repository's **Issues** tab and choose a task that matches your interests.
8. 🎉 Start hacking!

---

# Acknowledgments

BrainHack promotes collaborative, open-source scientific software development.

Meaningful contributions will be acknowledged appropriately in future software releases, conference presentations, preprints, and publications in accordance with standard scientific authorship and contribution practices.
