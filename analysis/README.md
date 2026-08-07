# BIOMAP Analysis

## Overview

This directory contains the Python script that calculates BIOMAP behavioral measurements from DeepLabCut tracking data.

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

- `BIOMAP_SoundAssay_Analysis6.1.py`

This script represents the current laboratory workflow and serves as the starting point for BrainHack development.
