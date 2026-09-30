from tqdm import tqdm
import glob
import os
import json
import pandas as pd
import numpy as np
from scripts.quaternions_utilities import *

def process_log_folder(folder_path):
    # List all JSON files in the folder
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {folder_path}")

    # Initialize lists to store DataFrames
    df_tracking_list = []
    df_steps_list = []

    def process_steps(data, participant_id):
        """Process the steps data from JSON and return a formatted DataFrame."""

        # Create DataFrame from steps data
        df = pd.DataFrame(data['steps'])

        # Add condition column (Valid/Invalid)
        df['condition'] = np.where(df['soundIndex'] == df['toyIndex'], 'Valid', 'Invalid')

        # Add position column (Front/Rear/Other)
        df['position'] = np.where(df['toyIndex'].isin([1, 7]), 'Rear',
                                np.where(df['toyIndex'].isin([3, 5]), 'Front', 'Other'))

        # Drop unnecessary columns
        df.drop(columns=['lightIndex', 'lightTime'], errors='ignore', inplace=True)

        # Add lateralisation (Left/Right/Other)
        df['lateralisation'] = np.where(df['toyIndex'].isin([1, 3]), 'Left',
                                      np.where(df['toyIndex'].isin([7, 5]), 'Right', 'Other'))

        # Count number of distractors (0, 1, or 3)
        df['nb_dist'] = np.sum(df[['distractorIndex1', 'distractorIndex2', 'distractorIndex3']].ne(-1), axis=1)

        # Identify unique distractor
        df['distractor_unique'] = df[['distractorIndex1', 'distractorIndex2', 'distractorIndex3']].\
            apply(lambda row: next((x for x in row if x != -1), np.nan), axis=1)

        # Define distractor modality conditions
        near_conditions = (
            ((df['toyIndex'] == 1) & (df['distractor_unique'] == 3)) |
            ((df['toyIndex'] == 3) & (df['distractor_unique'] == 5)) |
            ((df['toyIndex'] == 5) & (df['distractor_unique'] == 3)) |
            ((df['toyIndex'] == 7) & (df['distractor_unique'] == 5))
        )

        far_conditions = (
            ((df['toyIndex'] == 1) & (df['distractor_unique'] == 5)) |
            ((df['toyIndex'] == 3) & (df['distractor_unique'] == 7)) |
            ((df['toyIndex'] == 5) & (df['distractor_unique'] == 1)) |
            ((df['toyIndex'] == 7) & (df['distractor_unique'] == 3))
        )

        # Add modality column
        df['moda_dist'] = np.where(
            df['nb_dist'] == 1,
            np.where(near_conditions, 'Near',
                   np.where(far_conditions, 'Far', 'None')),
            'DA'  # DA = Doesn't Apply
        )

        # Clean up
        df.drop(columns=['distractor_unique'], inplace=True)

        # Format nb_dist column with more descriptive values
        df['nb_dist'] = np.where(
            df['nb_dist'] == 0, 'Zero',
            np.where(
                df['nb_dist'] == 3, 'Three',
                np.where(
                    df['nb_dist'] == 1,
                    df['moda_dist'].apply(lambda x: f"One_{x.lower()}" if x != 'DA' else 'DA'),
                    df['nb_dist']
                )
            )
        )

        # Add participant ID
        df['participant'] = participant_id

        return df

    # Process each JSON file with progress bar
    for file_path in tqdm(json_files, desc="Processing JSON files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Extract participant ID from filename (assuming format like "participant_001.json")
                participant_id = os.path.splitext(os.path.basename(file_path))[0].split("_")[-1]

                # Process tracking data
                df_tracking = pd.DataFrame(data['tracking'])
                df_tracking["participant"] = participant_id
                df_tracking_list.append(df_tracking)

                # Process steps data
                df_steps = process_steps(data, participant_id)
                df_steps_list.append(df_steps)

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            continue

    # Combine all DataFrames
    if df_tracking_list:
        df_track = pd.concat(df_tracking_list, ignore_index=True)
    else:
        df_track = None

    if df_steps_list:
        df_step = pd.concat(df_steps_list, ignore_index=True)
    else:
        df_step = None

    if df_track is None or df_step is None:
        return None, None

    # --- Step 1: Prepare df_step ---
    # Calculate trial time windows with progress bar
    tqdm.pandas(desc="Calculating time windows")
    df_step['startTime'] = df_step['soundTime']
    df_step['endTime'] = df_step['startTime'] + df_step['responseTime']

    # Add trial numbers if they don't exist
    if 'trial' not in df_step.columns:
        df_step['trial'] = df_step.index + 1

    # Initialize columns to add
    for col in ['correct','condition', 'position', 'lateralisation', 'nb_dist', 'trial']:
        if col not in df_track.columns:
            df_track[col] = None

    # --- Step 2: Optimized trial assignment with progress bars ---
    def assign_trial_info(df_track, df_step):
        # Pre-sort data for faster processing
        df_track_sorted = df_track.sort_values(['participant', 'timeSinceStartup'])
        df_step_sorted = df_step.sort_values(['participant', 'startTime'])

        # Get unique participants
        participants = df_track['participant'].unique()

        # Process each participant with progress bar
        for participant in tqdm(participants, desc="Processing participants"):
            # Filter data for current participant
            track_mask = df_track_sorted['participant'] == participant
            step_mask = df_step_sorted['participant'] == participant

            participant_track = df_track_sorted[track_mask]
            participant_step = df_step_sorted[step_mask]

            # Convert to numpy arrays for faster processing
            track_times = participant_track['timeSinceStartup'].values
            track_indices = participant_track.index.values
            step_starts = participant_step['startTime'].values
            step_ends = participant_step['endTime'].values

            # Initialize output arrays
            corrects = np.full(len(participant_track), np.nan, dtype=object)
            conditions = np.full(len(participant_track), np.nan, dtype=object)
            positions = np.full(len(participant_track), np.nan, dtype=object)
            lateralisations = np.full(len(participant_track), np.nan, dtype=object)
            nb_dists = np.full(len(participant_track), np.nan, dtype=object)
            trials = np.full(len(participant_track), np.nan, dtype=object)

            # Iterate through each trial window
            for step_idx in range(len(participant_step)):
                start = step_starts[step_idx]
                end = step_ends[step_idx]

                # Find all tracking points within this trial window
                mask = (track_times >= start) & (track_times <= end)

                # Assign trial info to all matching tracking points
                if np.any(mask):
                    corrects[mask] = participant_step.iloc[step_idx]['correct']
                    conditions[mask] = participant_step.iloc[step_idx]['condition']
                    positions[mask] = participant_step.iloc[step_idx]['position']
                    lateralisations[mask] = participant_step.iloc[step_idx]['lateralisation']
                    nb_dists[mask] = participant_step.iloc[step_idx]['nb_dist']
                    trials[mask] = participant_step.iloc[step_idx]['trial']

            # Assign the values back to the dataframe
            df_track.loc[track_indices, 'correct'] = corrects
            df_track.loc[track_indices, 'condition'] = conditions
            df_track.loc[track_indices, 'position'] = positions
            df_track.loc[track_indices, 'lateralisation'] = lateralisations
            df_track.loc[track_indices, 'nb_dist'] = nb_dists
            df_track.loc[track_indices, 'trial'] = trials

        return df_track

    # Apply the optimized function
    df_track = assign_trial_info(df_track, df_step)

    return df_step, df_track

def process_rotation_log_to_dataframes(csv_path: str):
    df = pd.read_csv(csv_path)
    required = {"time_s", "dt_s", "qx", "qy", "qz", "qw"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df_track = pd.DataFrame({
        "timeSinceStartup": df["time_s"].astype(float),
        "dt":   df["dt_s"].astype(float),
        "rEyeRotX": df["qx"].astype(float),
        "rEyeRotY": df["qy"].astype(float),
        "rEyeRotZ": df["qz"].astype(float),
        "rEyeRotW": df["qw"].astype(float),
        "lEyeRotX": df["qx"].astype(float),
        "lEyeRotY": df["qy"].astype(float),
        "lEyeRotZ": df["qz"].astype(float),
        "lEyeRotW": df["qw"].astype(float),
        "condition": "Test",
        "trial": 1
    })

    # Compute yaw/pitch relative to first quaternion
    q_ref = np.array([df["qx"].iloc[0], df["qy"].iloc[0],
                      df["qz"].iloc[0], df["qw"].iloc[0]], dtype=float)
    q_ref_inv = quat_conj(q_ref)

    yaws, pitches = [], []
    for qx, qy, qz, qw in zip(df["qx"], df["qy"], df["qz"], df["qw"]):
        q_cur = np.array([qx, qy, qz, qw], dtype=float)
        q_rel = quat_mul(q_ref_inv, q_cur)
        y, p = yaw_pitch_from_quat(q_rel)   # your existing conversion
        yaws.append(y); pitches.append(p)

    df_track["rEyeYaw"] = yaws
    df_track["rEyePitch"] = pitches
    df_track["lEyeYaw"] = yaws
    df_track["lEyePitch"] = pitches

    # df_step = same as before
    start_time = float(df["time_s"].iloc[0])
    end_time   = float(df["time_s"].iloc[-1])
    duration   = end_time - start_time

    df_step = pd.DataFrame([{
        "trial": 1,
        "condition": "Test",
        "soundTime": start_time,
        "responseTime": duration,
        "startTime": start_time,
        "endTime": end_time,
    }])

    return df_step, df_track