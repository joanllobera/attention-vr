from scipy.spatial.distance import pdist, squareform
from skbio.stats.distance import DistanceMatrix, permanova
import pandas as pd
import numpy as np


# create a dwell time per column of interest
def compute_dwell_time_per_trial(df_trial, angle_roi, eyeside='Right'):
    '''
    Front case:
                 ┌───────(C1)───────┐
              (C8) Near         Interest (C2)
                 │                   │
          (C7)   │                   │   (C3)
                 │                   │
              (C6) Far           Third (C4)
                 └───────(C5)───────┘
    
    Rear case:
                 ┌───────(C1)───────┐
            (C8) Far             Near (C2)
                 │                   │
          (C7)   │                   │   (C3)
                 │                   │
            (C6) Third        Interest (C4)
                 └───────(C5)───────┘
    '''
    # Define the different pilars angle
    if df_trial['position'].iloc[0] == 'Front':
        Interest_angle = 45
        Near_angle = -45
        Far_angle = -135
        Third_angle = 135
    elif df_trial['position'].iloc[0] == 'Rear':
        Interest_angle = 135
        Near_angle = 45
        Far_angle = -45
        Third_angle = -135

    # Get the dt to compute total time
    dt = np.mean(np.diff(df_trial['timeSinceStartup']))

    # Compute dwell time for each pilars
    if eyeside=='Right': eye_value = 'rEyeYaw'
    elif eyeside=='Left': eye_value= 'lEyeYaw'
    mask = lambda angle: np.abs((df_trial[eye_value] - angle + 180) % 360 - 180) <= angle_roi
    dwell_times = {
        "Interest_dwell_time": dt * mask(Interest_angle).sum(),
        "Near_dwell_time": dt * mask(Near_angle).sum(),
        "Far_dwell_time": dt * mask(Far_angle).sum(),
        "Third_dwell_time": dt * mask(Third_angle).sum(),
        "dt": dt
    }

    return pd.Series(dwell_times)

def get_object_time(df_trial, eyeside='Right'):
    '''
    Front case:
    angle_roi == 5°
                 ┌───────(C1)───────┐
              (C8) Near         Interest (C2)
                 │                   │
          (C7)   │                   │   (C3)
                 │                   │
              (C6) Far           Third (C4)
                 └───────(C5)───────┘
    
    Rear case:
    angle_roi == 5°
                 ┌───────(C1)───────┐
            (C8) Far             Near (C2)
                 │                   │
          (C7)   │                   │   (C3)
                 │                   │
            (C6) Third        Interest (C4)
                 └───────(C5)───────┘

    
    '''
    # Define the different pilars angle
    if df_trial['position'].iloc[0] == 'Front':
        angle_roi = 5
        Interest_angle = 45
        Near_angle = -45
        Far_angle = -135
        Third_angle = 135
    elif df_trial['position'].iloc[0] == 'Rear':
        angle_roi = 5
        Interest_angle = 135
        Near_angle = 45
        Far_angle = -45
        Third_angle = -135

    # Get the dt to compute total time
    dt = np.mean(np.diff(df_trial['timeSinceStartup']))

    # sort timings
    times = np.sort(df_trial['timeSinceStartup'])

    # get intersting timings
    start = times[0]
    stop = times[-1]
    reaction_time = stop-start
    object_first_fixation = None
    object_time = None

    # Compute first object fixation
    if eyeside=='Right': eye_value = 'rEyeYaw'
    elif eyeside=='Left': eye_value= 'lEyeYaw'
    mask = lambda angle: np.abs((df_trial[eye_value] - angle + 180) % 360 - 180) <= angle_roi
    object_first_fixation_id = mask(Interest_angle).argmax() if mask(Interest_angle).any() else None
    if object_first_fixation_id == None:
        object_first_fixation = np.nan
        object_time = np.nan
    else:
        object_first_fixation = times[object_first_fixation_id]
        object_time = object_first_fixation - start
    
    interesting_times = {
        "object_time": object_time,
        "reaction_time": reaction_time
    }
    return pd.Series(interesting_times)

def run_permanova(
    df,
    feature_cols,
    group_col,
    metric="euclidean",
    permutations=999
):
    """
    df           : DataFrame avec une ligne par trial
    feature_cols : liste de colonnes numériques (tes 4 dwell times)
    group_col    : colonne contenant les conditions (factor)
    metric       : distance pour pdist ('euclidean', 'braycurtis', etc.)
    """


    # 1) Matrice de features
    X = df[feature_cols].to_numpy()

    # 2) Distances
    d_vec = pdist(X, metric=metric)
    d_mat = squareform(d_vec)

    # 3) DistanceMatrix skbio
    dm = DistanceMatrix(d_mat, ids=df.index.astype(str))

    # 4) Groupes (condition)
    groups = df[group_col].values

    res = permanova(dm, grouping=groups, permutations=permutations)

    return res