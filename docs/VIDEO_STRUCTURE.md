# BIOMAP Video Structure

## Overview

BIOMAP behavioral videos contain a no-sound baseline period followed by alternating sound and silence periods.

The order of sound levels is randomized across experimental days. Therefore, the analysis pipeline cannot assume that sound levels always occur in the same sequence.

A metadata file is needed to describe the order and timing of experimental conditions for each recording.

---

# Experimental Timeline

Each recording begins with a 10-minute baseline period with no sound.

This is followed by multiple 2-minute sound presentations. Each sound presentation is followed by a 2-minute silence period.

A simplified recording may look like:

```text
10 minutes
Baseline — No Sound
        │
        ▼
2 minutes
Sound Level A
        │
        ▼
2 minutes
Silence
        │
        ▼
2 minutes
Sound Level B
        │
        ▼
2 minutes
Silence
        │
        ▼
2 minutes
Sound Level C
        │
        ▼
2 minutes
Silence
        │
        ▼
...
```

The order of Sound Level A, Sound Level B, Sound Level C, and later conditions is randomized for each experimental day.

For example:

```text
Experiment Day 1:
Baseline → 90 dB → Silence → 70 dB → Silence → 110 dB → Silence

Experiment Day 2:
Baseline → 110 dB → Silence → 90 dB → Silence → 70 dB → Silence
```

---

# Why Randomized Sound Order Matters

The pipeline cannot assign conditions based only on their position in the video.

For example, the first sound period cannot automatically be labeled `70_dB`, because it may be `90_dB`, `100_dB`, or another level depending on the randomized experimental order.

Each recording therefore requires metadata describing:

- Video identity
- Experimental date
- Sound-level order
- Start time or start frame for each epoch
- End time or end frame for each epoch
- Silence periods
- Baseline period
- Any excluded or interrupted periods

---

# Experimental Epochs

An epoch is a defined period of the video associated with one experimental condition.

Typical BIOMAP epochs include:

- Baseline
- Sound presentation
- Silence after sound
- Additional sound presentation
- Additional silence period

Each epoch should have:

- A unique order number
- A condition label
- A start frame
- An end frame
- A duration
- Any relevant notes

---

# Example Metadata File

A CSV file may be used to define the experimental epochs.

```csv
video_id,file_name,epoch_order,condition,start_frame,end_frame,duration_s
mouse01,mouse01.mp4,1,baseline,0,18000,600
mouse01,mouse01.mp4,2,90_dB,18001,21600,120
mouse01,mouse01.mp4,3,silence_after_90,21601,25200,120
mouse01,mouse01.mp4,4,110_dB,25201,28800,120
mouse01,mouse01.mp4,5,silence_after_110,28801,32400,120
```

This example assumes a frame rate of 30 frames per second.

The actual frame numbers must be based on the recording's verified frame rate and experimental timing.

---

# Start and Stop Frames

The current BIOMAP analysis script requires the user to enter start and stop frames for each experimental condition.

The desired pipeline should instead read these values from metadata.

Possible approaches include:

1. Manually create a metadata file after each experiment.
2. Export event timestamps from the acquisition software.
3. Convert recorded timestamps into video frame numbers.
4. Automatically detect experimental events if a synchronized trigger is available.

The most appropriate approach will depend on the available acquisition records.

---

# Baseline Period

The baseline is a 10-minute period with no sound.

It is used as the reference condition for calculating behavioral change during later sound and silence epochs.

For many measurements, the pipeline calculates:

```text
Percent Change from Baseline
```

for each experimental condition.

---

# Comparing the Baseline with 2-Minute Epochs

The baseline is 10 minutes long, while sound and silence epochs are 2 minutes long.

For measurements expressed as averages, ratios, angles, percentages, or other values that are not inherently duration-dependent, the baseline summary may be compared directly with condition-specific summaries using the established BIOMAP method.

For count-based measures, the duration difference must be handled explicitly.

---

# Nose-Tip Crossing Example

The nose-tip crossing output is cumulative across the video.

Suppose:

```text
Cumulative crossings at the end of baseline: 45
Cumulative crossings at the end of 90 dB:    67
```

The number of crossings during the 90 dB epoch is:

```text
67 - 45 = 22 crossings
```

The 10-minute baseline must also be converted to a 2-minute equivalent.

Because 10 minutes contains five 2-minute periods:

```text
45 ÷ 5 = 9 crossings per 2 minutes
```

The comparison is therefore:

```text
Baseline: 9 crossings per 2 minutes
90 dB:   22 crossings per 2 minutes
```

---

# Later Epochs

For every later condition, the number of crossings within that epoch is calculated by subtracting the cumulative count at the start of the epoch from the cumulative count at the end.

Example:

```text
End of baseline:             45
End of 90 dB:                67
End of silence after 90 dB:  81
End of 110 dB:              100
```

Condition-specific crossing counts are:

```text
Baseline, 2-minute equivalent: 45 ÷ 5 = 9
90 dB:                         67 - 45 = 22
Silence after 90 dB:           81 - 67 = 14
110 dB:                       100 - 81 = 19
```

---

# Baseline Normalization

The desired pipeline should calculate baseline-normalized behavioral measurements for each condition.

For a measurement expressed as percent change from baseline:

```text
Percent Change =
((Condition Value - Baseline Value) / Baseline Value) × 100
```

The exact sign convention and calculation method should remain consistent with the existing BIOMAP analysis script.

The pipeline should preserve:

- Raw baseline value
- Raw condition value
- Corrected condition value, when applicable
- Percent change from baseline
- Experimental condition label

---

# Recommended Metadata Fields

A video-level metadata file may include:

```text
video_id
file_name
mouse_id
experimental_date
experimental_group
sex
frame_rate
baseline_start
baseline_end
sound_order
notes
```

An epoch-level metadata file may include:

```text
video_id
epoch_order
condition
sound_level_db
epoch_type
start_frame
end_frame
duration_s
preceding_condition
exclude
notes
```

---

# Example Epoch-Level Metadata

```csv
video_id,epoch_order,condition,sound_level_db,epoch_type,start_frame,end_frame,duration_s,exclude
mouse01,1,baseline,,baseline,0,18000,600,false
mouse01,2,90_dB,90,sound,18001,21600,120,false
mouse01,3,silence_after_90,,silence,21601,25200,120,false
mouse01,4,110_dB,110,sound,25201,28800,120,false
mouse01,5,silence_after_110,,silence,28801,32400,120,false
```

---

# Validation Checks

Before analysis, the pipeline should verify that:

- Every video has metadata.
- Every epoch has a start and end frame.
- Epochs do not overlap.
- Epochs occur in chronological order.
- End frames are greater than start frames.
- Frame ranges do not exceed the video length.
- The baseline duration is approximately 10 minutes.
- Sound and silence durations are approximately 2 minutes.
- Every sound epoch has the correct sound-level label.
- Randomized sound order is preserved.
- Excluded epochs are clearly marked.
- The frame rate is known.

---

# BrainHack Opportunities

Potential BrainHack tasks include:

- Designing the metadata schema
- Creating metadata templates
- Validating metadata automatically
- Converting timestamps to frame numbers
- Detecting missing or overlapping epochs
- Matching videos to metadata files
- Automating nose-tip crossing correction
- Generating a visual timeline for each recording
- Producing warnings for incorrect epoch durations

---

# Desired Outcome

The user should not need to manually enter start and stop frames every time the BIOMAP analysis script is run.

Instead, the user should provide:

```bash
biomap analyze \
    --input data/raw_videos/ \
    --metadata data/video_manifest.csv
```

The pipeline should then use the metadata to identify every baseline, sound, and silence epoch automatically.
