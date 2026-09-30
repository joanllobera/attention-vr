## Overview
This project is designed to centralize raw VR headset data, eye-tracking analyses, and reaction time data processing .

It consists of three main components:

    - Storage of raw experimental data logs
    - Eye-tracking analysis pipelines
    - Reaction time processing and statistical analysis pipelines

Each component serves a distinct purpose but relies on a shared data structure derived from VR headset logs.

## Repository Structure
---
```
├── 1. performances analysis/  
│    ├──1.1. 1.1.ProcessingData_script.ipynb        # notebook for reaction time and accuracy data loading, cleaning, processing
│    │                                                 #### all dataframes are created from this script
│    ├── 1.2. R_analysis/
│    │      └── performances-analysis              # R script for reaction time and accuracy analysis
│    │      └── dataframes
├── 2. eyetracking analysis/
│    ├── fig                                       # figures from the script get loaded here
│    ├── Scripts/                                  # called in the main notebook
│    │      ├── process_eye_quaternions.py            # Converts eye rotation quaternions → yaw & pitch angles
│    │      ├── quaternions_utilities.py              # Quaternion operations & conversions
│    │      ├── process_log_folder.py                 # Loads VR headset logs and converts them into dataframes
│    │      └── visualizations.py                     # Plotting functions: heatmaps, histograms, temporal figures
│    ├── analysis.ipynb                            # **Main notebook** for data loading, cleaning, and visualization of eyetracking data
└── Logs

```

---

## 1. performances analysis
The reaction time pipeline processes VR headset logs to produce clean, interpretable behavioral datasets suitable for statistical analysis.
At the raw data level, it:
    - Parses VR headset event logs
    - Sorts events into trials
    - Extracts response times and correctness
    - Removes invalid trials (e.g., missing responses or implausible timings)

This processing ensures that reaction time data are structured consistently across participants and conditions.

## 2. eyetracking analysis
The eye-tracking pipeline processes raw VR headset logs to extract and analyze gaze behavior.

Specifically, it:
    - Converts headset orientation data (quaternions) into interpretable gaze angles
    - Removes invalid or incomplete trials
    - Computes gaze distributions across experimental conditions
    - Visualizes gaze behavior using:
        - heatmaps
        - contour plots
        - temporal gaze evolution figures

This pipeline allows detailed investigation of spatial and temporal patterns of visual attention during the task.
