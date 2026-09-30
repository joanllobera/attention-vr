### Overview

This project contains a two-step analysis pipeline for behavioral data examining reaction times and accuracy in a cueing task with distractors.

The workflow is divided into:
    - Data Processing (Python)
    - Statistical Analysis & Visualization (R)

It is essential to run the **data processing** step first, as it generates the datasets required for all subsequent analyses.

### 1. Data Processing (Python) — Run This First
## Why this step comes first

Raw behavioral data are stored as JSON log files, which are not directly suitable for statistical analysis. The Python scripts in this folder transform these raw logs into clean, structured, and analysis-ready datasets.

Without this step, the R analysis scripts cannot run, as they depend on the exported Excel files generated here.

## What this step does 

The data processing pipeline:
    - Loads and concatenates raw JSON log files (one per participant)
    - Extracts experimental variables
    - Cleans reaction times (removes implausibly fast responses)
    - Computes:
        - Mean reaction times for correct trials
        - Accuracy rates per participant and condition
    - Recategorizes distractors (Present vs. Absent) for specific analyses
    - Exports cleaned datasets as Excel files

### 2. R Analysis — Run After Data Processing
## Why this step comes second

The R scripts use the Excel files generated during data processing to perform statistical modeling and visualization. They assume the data are already cleaned, structured, and aggregated at the participant level.

## What this step does
The R analysis pipeline:
    - Loads processed datasets from the data processing step
    - Computes descriptive statistics for reaction time and accuracy
    - Runs:
        - Repeated-measures ANOVAs
        - Linear mixed-effects models (participant as random effect)
        - Post-hoc comparisons using estimated marginal means
        - Calculates effect sizes
        - Visualization plots







###### SCRIPT README

### Processing data using python befor R analysis

### Overview
This Python notebook preprocesses raw behavioral data stored in JSON log files and converts them into clean, analysis-ready dataframes for subsequent statistical analyses in R.

The script:

    - Loads and concatenates participant log files
    - Extracts experimental conditions (cue validity, position, distractors)
        - Cleans reaction time data
        - Computes mean reaction times for correct trials
        - Computes accuracy rates per participant and condition
        - Recategorizes distractor conditions for simplified analyses
        - Exports finalized datasets as Excel files for use in R

This notebook is therefore the data preparation stage of the full analysis pipeline.

## Depedencies

Input Data :
    
    - Location: ../Logs/
        - Format: .json files
        - Each file corresponds to one participant
        - Each JSON file contains a list of trial-level dictionaries under the key steps
    - Key raw variables include:
        - toyIndex,soundIndex                       # Corresponds to the pillar where the sound / target is located
        - toyTime, soundTime                        # Corresponds at the time of apparition of the sound and toy, based from the start of the experiment
        - responseTime
        - correct
        - distractorIndex1, distractorIndex2, distractorIndex3 #corresponds to one near one far and three distractor

## Processing Steps
    1. Import and concatenate all participant log files.
    2. Extract experimental variables: cue validity, position (Front/Rear), lateralization, distractor number and distance.
            A custom function creates task-relevant variables:
                - Cue Validity
                    - Valid: soundIndex == toyIndex
                    - Invalid: mismatch between sound and toy indices
                - Position
                    - Front: toy indices 3 and 5
                    - Rear: toy indices 1 and 7
                - Lateralisation
                    - Left: toy indices 1 and 3
                    - Right: toy indices 5 and 7
                - Distractor Count
                    - Computed from the number of non--1 distractor indices
                    - Encoded as:
                        - Zero
                        - One_Near
                        - One_Far
                        - Three
                - Distractor Distance (Near vs Far)
                    - Computed based on spatial relationship between toy and distractor positions
                    - Only applies when exactly one distractor is present
                    - Otherwise labeled "DA" (does not apply)

    3. Clean reaction times by removing values below 100 ms.
    4. Compute mean reaction times for correct trials per participant and condition.
    5. Compute accuracy rates per participant and condition.
    6. Recategorize distractors into Present vs Absent conditions for front.            # Present = One Near and Three ; Absent = One Far and Zero
    7. Export cleaned datasets as Excel files.

## Output Files Summary
Present in file : dataframes
File Name	Description
    - df_success_trials.xlsx	  # Mean reaction times for correct trials
    - df_accuracy.xlsx	          # Accuracy rates per participant and condition
    - df_recat_acc.xlsx	          # Accuracy with distractors recategorized

## Notes & Assumptions
    - Reaction times below 100 ms are considered invalid
    - Accuracy is computed before RT filtering
    - Mean RTs are used at the participant level to avoid trial-count bias
    - Distractor spatial logic is hard-coded based on experimental layout

## Recommended Execution Order
    - Place all participant logs in ../Logs/
    - Import/install all needed packages
    - Run notebook top to bottom
    - Verify exported Excel files
    - Run R analysis scripts using the generated dataframes

## Requirements 
    - Python version: 3.12
    - Notebook format: Jupyter
