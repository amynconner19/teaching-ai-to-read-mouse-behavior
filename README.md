# Teaching AI to Read Mouse Behavior

> **BrainHack project:** Build an open-source pipeline that analyzes mouse behavior from raw video and improves classification of pain-related immobility versus sleep, rest, and quiet wakefulness.

## TL;DR

The Behavioral Inventory of Mouse Affective Pain (**BIOMAP**) is a machine-learning-based behavioral assay developed in the Wood Lab. It combines computer vision, pose estimation, behavioral classification, and custom analyses to quantify pain-related behavior in freely moving mice.

During BrainHack, we will work toward a reproducible workflow that:

1. Accepts a raw behavioral video.
2. Runs the existing DeepLabCut and SimBA workflow.
3. Extracts BIOMAP behavioral features and pain-related metrics.
4. Produces standardized figures, reports, and machine-readable outputs.
5. Explores ways to distinguish pain-related immobility from sleep, rest, and quiet wakefulness.


## Why this matters

A standardized, open-source BIOMAP workflow could be easier to reproduce, audit, share, and adopt across laboratories. Although BIOMAP was developed to study sound-evoked pain, the resulting software may also support research in pain, behavior, neurodegeneration, movement disorders, drug discovery, and other areas that use automated behavioral phenotyping.

## BrainHack objectives

### Objective 1: Build an end-to-end behavioral analysis pipeline

Develop a reproducible workflow that takes a behavioral video as input and:

- Runs the existing DeepLabCut pose-estimation workflow
- Runs the existing SimBA feature-extraction and classification workflow
- Extracts BIOMAP features and pain-related metrics
- Generates standardized figures, summaries, and data files

**Stretch goal:** Reduce the workflow to a single command, notebook, or simple interface.

### Objective 2: Improve behavioral-state classification

Explore methods for distinguishing:

- Pain-related immobility
- Sleep
- Rest
- Quiet wakefulness
- Other low-movement states

Potential features include pose, posture, velocity, acceleration, head position, facial features, bout duration, temporal context, and breathing-related motion when visible.

The weekend goal is to establish useful baselines, identify promising features, and define next steps. A fully validated classifier is not expected.

## Current BIOMAP workflow

BIOMAP currently combines:

- **DeepLabCut** for markerless pose estimation
- **SimBA** for behavioral feature extraction and supervised classification
- **Custom code** for BIOMAP features, pain metrics, summaries, and visualization

The current workflow requires manual transitions between several software tools. One major goal is to connect these steps into a reproducible pipeline.

## Contributor tracks

| Track | Example tasks | Helpful skills |
|---|---|---|
| Pipeline engineering | Connect stages, configuration, logging, command-line workflow | Python, software engineering |
| DeepLabCut integration | Standardize video input and pose outputs | DeepLabCut, computer vision |
| SimBA integration | Automate feature extraction and classifier execution | SimBA, behavioral analysis |
| Behavioral classification | Build baseline models for inactive states | Machine learning, time series, statistics |
| Visualization | Standardize plots, summaries, and quality-control reports | pandas, matplotlib |
| Validation | Define test cases, expected outputs, and metrics | Testing, statistics, neuroscience |

Participants do not need experience in every area.
