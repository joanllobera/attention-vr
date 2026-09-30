from scripts.quaternions_utilities import *
import numpy as np

def add_eye_yaw_pitch(df_track):
    """
    Compute yaw and pitch from eye rotation quaternions in the dataframe.
    Adds 'rEyeYaw', 'rEyePitch', 'lEyeYaw', 'lEyePitch' columns to df_track.
    """
    # Compute Pitch and Yaw from quaternions 
    quats_all_r = np.stack([
        df_track['rEyeRotX'].to_numpy(),
        df_track['rEyeRotY'].to_numpy(),
        df_track['rEyeRotZ'].to_numpy(),
        df_track['rEyeRotW'].to_numpy()
    ], axis=1)
    quats_all_l = np.stack([
        df_track['lEyeRotX'].to_numpy(),
        df_track['lEyeRotY'].to_numpy(),
        df_track['lEyeRotZ'].to_numpy(),
        df_track['lEyeRotW'].to_numpy()
    ], axis=1)

    df_track['rEyeYaw'],df_track['rEyePitch'] =yaw_pitch_from_quat(quats_all_r)
    df_track['lEyeYaw'],df_track['lEyePitch'] =yaw_pitch_from_quat(quats_all_l)

    return df_track