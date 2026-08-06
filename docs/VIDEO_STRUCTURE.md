# BIOMAP Video Structure

## Overview

Each behavioral recording contains a baseline period followed by multiple sound presentations.

The order of sound levels is randomized for each experiment.

## Experimental Timeline

10 minutes
Baseline (no sound)

↓

2 minutes
Sound level A

↓

2 minutes
Silence

↓

2 minutes
Sound level B

↓

2 minutes
Silence

↓

...

The order of sound levels is randomized for every recording.

## Why this matters

The BIOMAP analysis script requires the start and stop frame for each experimental epoch in order to calculate:

- baseline values
- sound-evoked responses
- percent change from baseline

Automating epoch detection and metadata handling is an important future goal.
