# BIOMAP Pipeline Components

## Overview

The BIOMAP workflow currently consists of several independent software tools, scripts, and manual analysis steps.

The goal of this document is to break the full workflow into smaller components that BrainHack participants can understand, improve, and automate.

Each component represents a possible contribution area. The project does not require every component to be completed during one weekend.

---

# Pipeline Summary

```text
Batch of Behavioral Videos
            │
            ▼
Input Validation & Metadata
            │
            ▼
Run Trained DeepLabCut Models
            │
            ▼
Generate Tracking CSV Files
            │
      ┌─────┴─────┐
      │           │
      ▼           ▼
BIOMAP Analysis   SimBA Analysis
      │           │
      ▼           ▼
Facial & Body     Complex Behavioral
Measurements      Measurements
      │           │
      └─────┬─────┘
            ▼
Baseline Normalization
            │
            ▼
Post-Processing Corrections
            │
            ▼
Composite Score Calculation
            │
            ▼
Figure Generation
            │
            ▼
Analysis-Ready Outputs
            │
            ▼
Quality-Control Reports
```

---

# Component 1: Input Videos and Metadata

## Current State

Behavioral videos are recorded in batches.

Each video contains:

- A 10-minute no-sound baseline
- Multiple 2-minute sound presentations
- A 2-minute silence period after each sound presentation
- A randomized order of sound levels across experimental days

The analysis currently requires users to manually provide:

- Video locations
- Start and stop frames
- Sound-level labels
- Output file names

## BrainHack Goal

Develop a standardized way to describe each video and its experimental epochs.

Possible outputs include:

- A metadata CSV file
- A YAML or JSON configuration file
- Automated video validation
- Automated frame-range calculation from timestamps

## Example Metadata

```csv
video_id,file_name,epoch_order,condition,start_frame,end_frame
mouse01,mouse01.mp4,1,baseline,0,18000
mouse01,mouse01.mp4,2,90_dB,18001,21600
mouse01,mouse01.mp4,3,silence_after_90,21601,25200
mouse01,mouse01.mp4,4,110_dB,25201,28800
```

## Helpful Skills

- Python
- Data organization
- Experimental design
- CSV/YAML/JSON
- Video processing

---

# Component 2: DeepLabCut Batch Processing

## Current State

The lab currently uses two trained DeepLabCut projects:

1. A primary model for facial and body-position tracking
2. A secondary model for paw tracking

Each project is opened and run separately.

The models generate tracking outputs for the same batch of behavioral videos.

## BrainHack Goal

Automate execution of both trained DeepLabCut models across a batch of videos.

The pipeline should:

- Load the correct trained project configurations
- Run both models on every video
- Generate tracking CSV or H5 files
- Preserve consistent video names
- Organize outputs by video and model
- Record processing status and errors

## Possible Output Structure

```text
intermediate/
└── deeplabcut/
    ├── facial_body/
    │   ├── mouse01_tracking.csv
    │   └── mouse02_tracking.csv
    │
    └── paws/
        ├── mouse01_tracking.csv
        └── mouse02_tracking.csv
```

## Helpful Skills

- DeepLabCut
- Python
- Batch processing
- File-system organization
- Computer vision

---

# Component 3: DeepLabCut Quality Control

## Current State

Tracking quality may be reviewed through DeepLabCut outputs or labeled videos, but quality-control procedures are not yet integrated into a single automated report.

## BrainHack Goal

Develop automated tracking-quality checks.

Potential checks include:

- Low-likelihood body-part detections
- Missing coordinates
- Implausible coordinate jumps
- Body-part overlap
- Prolonged tracking loss
- Video/model mismatches
- Labeled quality-control video generation

## Potential Outputs

```text
quality_control/
├── tracking_summary.csv
├── flagged_frames.csv
├── flagged_videos.csv
└── labeled_videos/
```

## Helpful Skills

- DeepLabCut
- Python
- Data visualization
- Quality assurance
- Computer vision

---

# Component 4: BIOMAP Individual Measurement Calculation

## Current State

The primary DeepLabCut tracking CSV is passed to an existing Python analysis script.

The user currently enters:

- The tracking CSV location
- Start and stop frames for each condition
- The desired output file name

The script calculates individual facial and body-position measurements and returns percent change from baseline for each sound-level condition.

## Facial-Grimace Measurements

- Ear Ratio
- Ear Position
- Ear Tip Tilt
- Eye Ratio
- Snout Position
- Mouth Position

## Body-Position Measurements

- Relative Nose Tip Position
- Percent of Nose Tip in Top Region
- Nose-Tip or Vertical Line Crosses
- Face Inclination

## BrainHack Goal

Integrate the existing analysis script into the automated pipeline.

The pipeline should:

- Read metadata automatically
- Identify the correct frames for each condition
- Run the existing measurement calculations
- Process multiple videos in a batch
- Produce standardized output files
- Record any failures or missing values

## Helpful Skills

- Python
- pandas
- Numerical analysis
- Geometry
- Behavioral neuroscience

---

# Component 5: Baseline Normalization

## Current State

The existing BIOMAP analysis script calculates percent change from baseline for each facial and body-position measurement during each sound-level condition.

## BrainHack Goal

Ensure baseline normalization is:

- Automated
- Consistent
- Documented
- Tested
- Applied correctly to every experimental condition

The pipeline should preserve:

- Raw measurements
- Baseline values
- Condition-specific values
- Percent change from baseline

## Important Consideration

The baseline period is 10 minutes, while sound and silence epochs are 2 minutes.

Any rate- or count-based metric must be converted to an equivalent 2-minute baseline value before comparison.

## Helpful Skills

- Python
- Statistics
- Experimental design
- Data validation

---

# Component 6: Nose-Tip Crossing Correction

## Current State

The nose-tip crossing output is cumulative across the video and requires manual correction.

For example:

```text
End of 10-minute baseline: 45 cumulative crossings
End of 90 dB epoch:        67 cumulative crossings
```

The number of crossings during the 90 dB epoch is:

```text
67 - 45 = 22 crossings
```

Because the baseline is 10 minutes and the comparison epochs are 2 minutes, the baseline must be converted to a 2-minute equivalent:

```text
45 ÷ 5 = 9 crossings per 2 minutes
```

The 90 dB condition is therefore compared with a baseline value of 9 crossings per 2 minutes.

For later epochs, the pipeline must subtract the cumulative count at the start of the epoch from the count at the end.

## BrainHack Goal

Automate conversion of cumulative nose-tip crossing values into condition-specific counts.

The pipeline should:

- Identify epoch boundaries from metadata
- Calculate crossings within each epoch
- Convert the 10-minute baseline to a 2-minute equivalent
- Preserve both cumulative and corrected values
- Flag impossible or negative counts

## Helpful Skills

- Python
- Time-series analysis
- Data validation
- Experimental design

---

# Component 7: Composite Score Calculation

## Current State

Composite scores are currently calculated manually.

For each sound-level condition:

- Six facial-grimace measurements are added to create a Facial Grimace Score
- Four body-position measurements are added to create a Body Position Score

The individual measurements have already been expressed as percent change from baseline before being combined.

## BrainHack Goal

Automate composite score calculation.

The pipeline should:

- Confirm that all required measurements are present
- Apply the correct direction or sign convention
- Sum the six facial measurements
- Sum the four body-position measurements
- Preserve the individual components
- Produce one score per video and condition
- Flag incomplete scores

## Outputs

```text
facial_grimace_scores.csv
body_position_scores.csv
```

## Helpful Skills

- Python
- pandas
- Behavioral analysis
- Testing
- Data validation

---

# Component 8: SimBA Integration

## Current State

The tracking CSV from the primary DeepLabCut model and the tracking CSV from the paw model are imported into SimBA.

SimBA is then used to calculate complex behavioral measures, including:

- Grooming
- Rearing
- Pausing
- Respiration rate

The current workflow requires manual interaction with the SimBA interface.

## BrainHack Goal

Automate the established SimBA analysis workflow.

The pipeline should:

- Match the two tracking files to the correct video
- Validate naming conventions
- Import required tracking data
- Run the established SimBA project and classifiers
- Export complex-behavior outputs
- Record failures and warnings

## Important Question

The project should not assume that complex behaviors are combined into a single composite score unless the scientific scoring method is defined and approved.

## Helpful Skills

- SimBA
- Python
- Behavioral classification
- Machine learning
- File management

---

# Component 9: Figure Generation

## Current State

Figures are currently generated manually after the analysis outputs are produced.

## BrainHack Goal

Automatically generate standardized figures for:

### Individual Facial Measurements

- Ear Ratio
- Ear Position
- Ear Tip Tilt
- Eye Ratio
- Snout Position
- Mouth Position

### Individual Body-Position Measurements

- Relative Nose Tip Position
- Percent in Top
- Nose-Tip Crossings
- Face Inclination

### Composite Scores

- Facial Grimace Score
- Body Position Score

### Complex Behaviors

- Grooming
- Rearing
- Pausing
- Respiration rate

## Figure Requirements

Figures should:

- Use consistent labels
- Preserve randomized sound-level order correctly
- Show baseline-normalized values
- Include sample-size information when available
- Be reproducible from saved data
- Be exportable in publication-quality formats

## Helpful Skills

- matplotlib
- pandas
- Plotly
- Scientific visualization
- Data analysis

---

# Component 10: Analysis-Ready Data Export

## Current State

Data are transferred manually into downstream analysis and plotting software, including GraphPad Prism.

## BrainHack Goal

Generate standardized tables that can be imported into:

- GraphPad Prism
- R
- Python
- Other statistical software

## Potential Outputs

```text
results/
├── individual_facial_metrics.csv
├── individual_body_metrics.csv
├── complex_behavior_metrics.csv
├── facial_grimace_scores.csv
├── body_position_scores.csv
└── batch_summary.csv
```

## Helpful Skills

- pandas
- Data organization
- Statistics
- Reproducible research

---

# Component 11: Reporting and Logging

## Current State

The workflow does not yet produce one consolidated processing report.

## BrainHack Goal

Generate a report summarizing:

- Videos processed
- Models used
- Conditions detected
- Successful analyses
- Warnings
- Failed videos
- Missing outputs
- Quality-control flags
- Software versions
- Configuration settings

## Potential Outputs

```text
processing_log.txt
batch_summary.csv
summary_report.html
```

## Helpful Skills

- Python
- Logging
- HTML reporting
- Software testing
- Reproducibility

---

# Suggested BrainHack Priorities

## High Priority

1. Standardize video metadata and epoch definitions
2. Automate both trained DeepLabCut models
3. Integrate the existing BIOMAP analysis script
4. Automate nose-tip crossing correction
5. Automate composite score calculation
6. Generate standardized figures

## Medium Priority

1. Automate SimBA execution
2. Build quality-control reports
3. Standardize output tables
4. Improve installation and onboarding documentation

## Stretch Goals

1. Create a complete command-line interface
2. Generate an HTML summary report
3. Add automated tests
4. Improve inactive-state classification
5. Support additional experimental designs

---

# Definition of Success

A successful BrainHack contribution does not need to solve the entire pipeline.

A useful contribution may be:

- One automated processing step
- A tested helper function
- A standardized metadata format
- A quality-control check
- A reproducible figure
- Improved documentation
- A clearly documented limitation
- A well-defined follow-up issue

The long-term objective is to connect these components into a single command:

```bash
biomap analyze data/raw_videos/
```
