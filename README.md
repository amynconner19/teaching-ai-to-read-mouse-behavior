# Teaching AI to Read Mouse Behavior

## TL;DR

> **BrainHack Project:** Build an open-source, end-to-end BIOMAP pipeline that transforms batches of mouse behavioral videos into publication-ready figures and analysis-ready datasets.

---

# Overview

The **Behavioral Inventory of Mouse Affective Pain (BIOMAP)** is a machine learning–based behavioral assay developed in the Wood Lab that quantifies pain-related behavior in freely moving mice using computer vision, pose estimation, behavioral classification, and custom analysis.

BIOMAP currently combines **DeepLabCut**, **SimBA**, and custom Python scripts, but many downstream analyses, including data processing, figure generation, and statistical preparation, still require manual effort.

This BrainHack project aims to build a reproducible, open-source pipeline that automates the entire workflow, allowing researchers to process batches of behavioral videos with minimal user interaction.

---

# Why This Matters

Behavioral phenotyping often requires researchers to move data between multiple software packages, perform manual calculations, and generate figures by hand.

Automating BIOMAP will:

- Improve reproducibility
- Reduce manual processing
- Standardize analyses
- Simplify onboarding
- Enable larger behavioral datasets
- Support collaborative software development

Although originally developed to study sound-evoked pain, the resulting software could support a broad range of behavioral neuroscience applications.

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
                  Manual Statistics
```

For additional details, see:

- [Current Workflow](docs/CURRENT_WORKFLOW.md)
  
---

# Long-Term Vision

Our goal is for an entire experiment to be analyzed with a single command:

```bash
biomap analyze data/raw_videos/
```

The pipeline would automatically:

- Process batches of behavioral videos
- Run trained DeepLabCut models
- Perform behavioral classification with SimBA
- Calculate normalized behavioral metrics and composite scores
- Apply post-processing and quality-control steps
- Generate publication-quality figures
- Export analysis-ready datasets

allowing researchers to focus on scientific interpretation rather than data processing.

---

# BrainHack Objectives

## Objective 1 — End-to-End Pipeline

Develop an automated workflow that processes batches of behavioral videos with minimal user interaction.

Potential tasks include:

- Automating DeepLabCut execution
- Running SimBA within the pipeline
- Organizing intermediate files
- Calculating normalized behavioral metrics
- Computing composite scores
- Generating standardized figures
- Exporting analysis-ready tables

---

## Objective 2 — Behavioral-State Classification

Explore methods for improving classification of inactive behavioral states, including:

- Pain-related immobility
- Sleep
- Rest
- Quiet wakefulness

Potential approaches include:

- Pose-estimation features
- Temporal modeling
- Machine learning
- Rule-based methods
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

Contributors are encouraged to work wherever their interests and expertise align.

| Track | Example Tasks | Helpful Skills |
|--------|---------------|----------------|
| Pipeline Engineering | Connect workflow components | Python, software engineering |
| DeepLabCut Integration | Automate trained DLC models | DeepLabCut, computer vision |
| SimBA Integration | Automate behavioral classification | SimBA, behavioral analysis |
| BIOMAP Analysis | Automate behavioral analyses | Python, data analysis |
| Figure Generation | Create publication-quality figures | matplotlib, Plotly |
| Quality Control | Build validation and QC reports | Statistics, testing |
| Documentation | Improve tutorials and onboarding | GitHub, Markdown |
| Experimental Design | Automate metadata and experimental structure | Neuroscience, data science |

**No prior experience with every component is expected.**

We welcome contributors from neuroscience, computer science, engineering, data science, machine learning, software engineering, and scientific visualization.

---

# Expected BrainHack Deliverables

The goal is **not** to complete the entire pipeline in one weekend.

Instead, we hope to:

- Automate key portions of the BIOMAP workflow
- Integrate existing software components
- Improve reproducibility and documentation
- Reduce manual analysis and figure generation
- Build tools that support future development

Every contribution—whether code, documentation, testing, visualization, or scientific insight—helps move BIOMAP toward a fully automated behavioral analysis platform.

---

# Getting Started

If you're new to the project:

1. 📖 Read the [BIOMAP bioRxiv Preprint](paper/BIOMAP_Biorxiv.pdf)
2. 🔬 Review the [Current Workflow](docs/CURRENT_WORKFLOW.md)
3. 🚀 Explore the [Desired Workflow](docs/DESIRED_WORKFLOW.md)
4. 💻 Install the required software using the [Software Overview](docs/software/README.md)
5. 📝 Browse the repository's **Issues** tab
6. 🎉 Start hacking!

---

# Acknowledgments

Contributors will be acknowledged appropriately in future software releases, conference presentations, preprints, and publications in accordance with standard scientific contribution and authorship practices.
