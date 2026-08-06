# BIOMAP Analysis and Figure Generation

## Overview

This module converts DeepLabCut pose-estimation outputs and, when applicable,
SimBA behavioral-classification outputs into BIOMAP behavioral measurements,
composite pain scores, quality-control outputs, and standardized figures.

## Inputs

- DeepLabCut tracking CSV or H5 files
- Video metadata and experimental epoch definitions
- Optional SimBA behavioral-classification outputs
- Baseline-period definitions
- Analysis configuration file

## Calculated facial-grimace measurements

- Ear Ratio
- Ear Position
- Ear Tip Tilt
- Eye Ratio
- Snout Position
- Mouth Position

## Calculated body-position measurements

- Relative Nose Tip Position
- Percent in Top
- Vertical Line Crosses
- Face Inclination

## Composite scores

Each individual measurement is summarized within defined epochs and normalized
relative to baseline. Facial measurements are combined into a Facial Grimace
Score, and body-position measurements are combined into a Body Position Score.

## Outputs

- Frame-level measurements
- Epoch-level summaries
- Facial Grimace Scores
- Body Position Scores
- Quality-control flags
- Standardized figures
- Machine-readable analysis reports

## BrainHack goal

The goal is to replace the existing collection of manual and project-specific
analysis steps with a tested, configurable, and reproducible module that can
process batches of experiments.
