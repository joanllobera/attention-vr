# Eye Tracking Analysis of Attention Experiment

## Getting Started

### Requirements
- Python 3.9+ (tested on 3.13) 
- Jupyter Notebook 


### Setup with Conda
1. Create the environment from the provided `environment.yml`:
   ```bash
   conda env create -f environment.yml
   conda activate eyevr
   ````
2.	Open and run Analysis.ipynb to reproduce the analysis.







## Overview
This project analyzes **eye-tracking data** from a VR experiment where participants focused on different **pillars** in a 3D environment.  

The pipeline processes VR headset logs, converts quaternions to interpretable gaze angles, removes invalid trials, and visualizes gaze distributions through heatmaps, contour plots, and temporal figures.  

---

## Repository Structure
```
├── Analysis.ipynb                # Main notebook for data loading, cleaning, and visualization and csv generation
├── Scripts/                       # FUNCTIONS for the main script "Analysis"
│   ├── process_eye_quaternions.py # Converts eye rotation quaternions → yaw & pitch angles
│   ├── quaternions_utilities.py   # Quaternion operations & conversions
│   ├── process_log_folder.py      # Loads VR headset logs and converts them into dataframes
│   └── visualizations.py          # Plotting functions: heatmaps, histograms, temporal figures
├── fig                            #figures generated are reported there
└── R_script_eyeTracking           # R script for statistical analysis
│   ├── Dataframes-used            # Dataframes generated in csv in "analysis" go there and are used in R scripts
│   ├── early_gaze_analysis.Rmd
│   ├── Gaze_onset_latency.Rmd
│   └── TimeToAOI.Rmd
```

---

## Analysis Workflow IN Python Script

### 1. Load Trials data
- JSON log files from the VR headset are parsed.  
- Eye rotation quaternions are converted into **yaw** and **pitch** angles in world coordinates.  

      # Data Cleaning

      Cleaned 88 / 3075 trials (2.86%) due to >50% zero rEyeYaw values.
      Trials removed (incorrect responses): 74
      Trials removed (participant 24 excluded): 129

      === Preprocessing Summary ===
      Participants retained : 19
      Trials retained       : 2784


### 2. Gaze distribution
      ## Figures
         Figure 5 in article, heatmap Valid/Invalid => change "condition =" to see either
         Figure 6 
         Figure 7 , gaze dispersion of valid or invald trials => change "data =" to get either
         Figure 8

      ## Statistical analysis on gaze distribution

### 3. Early gaze analysis
start of a trial is the soundTime = start of the sound cue, lasting 150 ms. Afterwhich target appears.
High number of samples because frequency of 50 Hz over 300 ms x 2784

Used the yaw in a 300 ms timeframe after trialStart. trialStart is obtained by subtracting the minimum timestamp (= the first sample of that trial) from every row in timeSinceStartUp. 


### 4. Gaze onset latency dataframe
Chose a 15° radius aroud the fixation cross = treshold
Ordered by time 
The sample that exceded the tresholds were recorded using the participant, condition position and nb_dist
A dataframe is generated for analysis on R

### 5. Time to reach AOI
Returns a dictionnary with:
      - first_entry_time : when gaze first entered the AOI (ms), or NaN
      - visits           : list of dicts {entry_time, exit_time, duration}
      - total_dwell      : total time spent in AOI across all visits (ms)

targte mapping : are of the target : found by looking at gazes on correct detection. Corresponds to the area in unity.

Total trials: 2784
NaN first_entry_ms: 188
NaN total_dwell_ms: 0

NaN rate: 6.8%



---

 

