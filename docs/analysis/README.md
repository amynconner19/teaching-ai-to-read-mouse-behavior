# BIOMAP Analysis

## Overview

This directory contains the Python scripts that calculate BIOMAP behavioral measurements from DeepLabCut tracking data and generate the outputs used for downstream analysis.

The current workflow is implemented as a standalone analysis script. During BrainHack, the goal is to refactor this workflow into a modular, automated component of the end-to-end BIOMAP pipeline.

---

## Current Workflow

The current analysis script:

- Reads DeepLabCut tracking CSV files
- Calculates facial and body-position measurements
- Computes percent change from baseline for each sound-level condition
- Exports summary CSV files for downstream analysis

Additional manual steps are currently required to:

- Correct nose-tip crossing measurements
- Calculate composite Facial Grimace and Body Position scores
- Generate publication-quality figures
- Perform statistical analyses

---

## Current Script

- [`BIOMAP_SoundAssay_Analysis6.1.py`](scripts/BIOMAP_SoundAssay_Analysis6.1.py)

This script represents the current laboratory workflow and serves as the starting point for BrainHack development.

---

## BrainHack Goal

The goal is to transform the existing analysis script into a reusable pipeline module that can:

- Process batches of experiments automatically
- Remove hard-coded inputs and experimental parameters
- Calculate composite scores automatically
- Generate standardized figures and reports
- Integrate seamlessly with DeepLabCut and SimBA
