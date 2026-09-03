# BIOMAP SimBA Model

This directory contains the existing SimBA project used to classify complex behaviors in the BIOMAP workflow.

The behavioral classifiers are already trained. No model creation or retraining is required.

## Project

```text
simba-model/BIOMAPComplexPawNosetip/
```

Before running the project, download the example behavioral video and complete the two DeepLabCut analyses described in the [DeepLabCut model instructions](../deeplabcut-models/README.md).

The resulting DeepLabCut tracking CSV files will be used as pose-estimation inputs for SimBA.

## Update the SimBA Project Paths

Open the SimBA configuration file:

```text
simba-model/BIOMAPComplexPawNosetip/project_folder/project_config.ini
```

The configuration file contains paths from the computer on which the project was originally created. Update these paths to match the location of the project on your computer.

### General Settings

Update `project_path`:

```ini
[General settings]

project_path = C:/Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/simba-model/BIOMAPComplexPawNosetip/project_folder

project_name = BIOMAPComplexPawNosetip

workflow_file_type = csv

animal_no = 1

os_system = Windows
```

### Machine-Learning Model Settings

Update `model_dir` and each `model_path`:

```ini
[SML settings]

model_dir = C:/Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/simba-model/BIOMAPComplexPawNosetip/models

model_path_1 = C:/Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/simba-model/BIOMAPComplexPawNosetip/models/generated_models/Grooming.sav

model_path_2 = C:/Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/simba-model/BIOMAPComplexPawNosetip/models/generated_models/Pausing.sav

model_path_3 = C:/Users/YourUsername/Desktop/teaching-ai-to-read-mouse-behavior/simba-model/BIOMAPComplexPawNosetip/models/generated_models/Rearing.sav
```

Replace `YourUsername` and the preceding folders with the actual location of the repository on your computer.

Keep the following settings unchanged:

```ini
project_name = BIOMAPComplexPawNosetip
workflow_file_type = csv
animal_no = 1
os_system = Windows
```

## Run the SimBA Analysis

Open SimBA and complete the following steps in order:

1. **Load the project**

   Select the updated configuration file:

   ```text
   simba-model/BIOMAPComplexPawNosetip/project_folder/project_config.ini
   ```

2. **Load the video**

   Add the example behavioral video downloaded from Google Drive.

3. **Import the DeepLabCut tracking data**

   Import the required tracking CSV output generated during the preceding DeepLabCut analyses.

4. **Set the video parameters**

   Open the **Video Parameters** tab and confirm the required parameters for the example video.

5. **Skip outlier correction**

   Open the **Outlier Correction** tab and select **Skip outlier correction**.

6. **Define the region of interest**

   Open the **ROI** tab and draw an ROI named:

   ```text
   AboveFloor
   ```

7. **Extract features**

   Open the **Extract Features** tab and run feature extraction.

8. **Append ROI data**

   After feature extraction, select **Append ROI data by body part** and use:

   ```text
   Body part 2: right_wrist
   Body part 4: left_wrist
   ```

9. **Run the trained behavioral classifiers**

   Run the existing machine-learning models for:

   * Grooming
   * Pausing
   * Rearing

## Output

After the classifiers finish running, SimBA will generate a machine-results CSV file for the video in:

```text
simba-model/BIOMAPComplexPawNosetip/project_folder/csv/machine_results/
```

This file contains the frame-by-frame results from the trained behavioral classifiers and is used in the subsequent BIOMAP analysis.

## Additional Resources

* [BIOMAP Pipeline Video Tutorial](../biomap-tutorial/README.md)
* [Current Manual BIOMAP Analysis Spreadsheet](https://docs.google.com/spreadsheets/d/1WkuiPLr_xq9GRXaTRGkcbiSxfqFsBzITJBM_5Ld6vMQ/edit?usp=sharing)

The video tutorial demonstrates the current SimBA workflow, including project loading, ROI creation, feature extraction, and classifier execution. The spreadsheet shows how the resulting machine-classification data are currently processed manually.

The BrainHack project goal is to automate these steps and integrate them into the complete BIOMAP analysis pipeline.
