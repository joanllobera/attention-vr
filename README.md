#  Attention orienting and serial search in virtual reality
## Abstract
 Orienting attention in space is crucial for efficient perception and learning.The cognitive and neural underpinnings of spatial attention have been extensively studied in tasks requiring focusing and shifting attention across locations. However, these studies mainly explored frontal 2D visual space. Here we designed a virtual reality (VR) environment combining a visual search task with a modified Posner orienting paradigm to investigate the deployment of attention in both front and rear locations, and compare performance with classic 2D findings. We combined response times with eye-tracking data recorded in the VR headset.
Twenty participants were asked to discriminate between 2 targets arranged in 4 locations around them. Targets were spatially cued (20% Valid, 80% Invalid), and presented with a varying number of identical distractors (Zero, One Near, One Far, Three) to additionally probe serial search. Target detection was faster in valid than invalid conditions, but delayed by distractors, in line with classic effects in Posner and search tasks, respectively. Eye-tracking data confirmed that attention shifts, as observed by gaze patterns over time, were tightly correlated with response times, and both were modulated by cue validity and distractor load. 
Our results confirm eye-tracking is a powerful tool in VR for quantifying attentional dynamics through overt gaze strategies. The behavioral and gaze data converge for targets appearing in rear or front space, suggesting that attentional orienting engages similar mechanisms of sensory competition and selection in a full 360° space (in both front and rear), supporting a functional continuity in space representation used to guide selective attention processes. 

## Overview
This repository centralizes raw VR headset data, eye-tracking analyses, and reaction time data processing.

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
