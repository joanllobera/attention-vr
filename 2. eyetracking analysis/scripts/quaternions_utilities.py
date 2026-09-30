import numpy as np


#now for the angles to be corrected
eps = 1e-8

def length(qx,qy,qz):
    return  np.sqrt( qx * qx + qy*qy + qz* qz ) 


def rad2deg( x):
    return x * 180.0 / np.pi

# -----------------------------
# Quaternion utilities
# -----------------------------

def quat_normalize(q):
    """
    Normalize quaternion(s).
    q shape: (..., 4) in (qx, qy, qz, qw).
    Returns array of same shape.
    """
    q = np.asarray(q, dtype=float)
    n = np.linalg.norm(q, axis=-1, keepdims=True)
    n = np.maximum(n, 1e-16)
    return q / n

def quat_conj(q):
    '''
    Quaternion conjugate.
    q shape: (..., 4) in (qx, qy, qz, qw).
    Returns array of same shape with vector part negated.
    '''
    q = np.asarray(q, dtype=float)
    conj = np.copy(q)
    conj[..., :3] *= -1.0
    return conj


def quat_mul(q1, q2):
    """"
    Hamilton product of quaternions.
    Both q1, q2 shape: (..., 4) in (qx, qy, qz, qw).
    Returns quaternion with broadcasted leading shape.
    """
    q1 = np.asarray(q1, dtype=float)
    q2 = np.asarray(q2, dtype=float)
    x1, y1, z1, w1 = np.moveaxis(q1, -1, 0)
    x2, y2, z2, w2 = np.moveaxis(q2, -1, 0)

    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2

    return np.moveaxis(np.stack([x, y, z, w], axis=0), 0, -1)


def quat_apply(q, v):
    """
    Rotate vector(s) v by quaternion(s) q (both can be batched).
    q: (..., 4) in (qx, qy, qz, qw).
    v: (..., 3).
    Returns rotated v with same leading shape.
    """
    q = np.asarray(q, dtype=float)
    v = np.asarray(v, dtype=float)

    # Unpack (qx, qy, qz, qw)
    x, y, z, w = np.moveaxis(q, -1, 0)

    # v’ = q v q^{-1} = v + 2w* cross(q_vec,v) + 2*cross(q_vec, cross(q_vec,v))
    # so lets compute it step by step

    # t = 2 * cross(q_vec, v)
    t = 2.0 * np.stack([
        y*v[...,2] - z*v[...,1],
        z*v[...,0] - x*v[...,2],
        x*v[...,1] - y*v[...,0]
    ], axis=-1)

    # v' = v + w*t + cross(q_vec, t)
    vp = v + w[..., None]*t + np.stack([
        y*t[...,2] - z*t[...,1],
        z*t[...,0] - x*t[...,2],
        x*t[...,1] - y*t[...,0]
    ], axis=-1)
    return vp

def yaw_pitch_from_quat(q):
    """
    Compute yaw (deg, [-180,180]) and pitch (deg, [-90,90]) of the gaze direction.
    Gaze direction is q * forward, with forward = (0,0,1) (Unity-style).
    q: (...,4) in (qx, qy, qz, qw)
    Returns: yaw, pitch as arrays matching q's leading shape.
    """
    q = quat_normalize(q)
    d = quat_apply(q, np.array([0.0, 0.0, 1.0]))  # gaze dir

    # yaw around Y (left/right), pitch around X (up/down)
    yaw_deg   = np.degrees(np.arctan2(d[...,0], d[...,2]))                     # uses x,z
    pitch_deg = np.degrees(np.arcsin(np.clip(d[...,1], -1.0, 1.0)))            # uses y
    return yaw_deg, pitch_deg

def uv_from_yaw_pitch(yaw_deg, pitch_deg, stretch_pitch_to_180=False):
    """
    Map yaw/pitch (deg) to UV in [0,1]^2 for an equirectangular grid.
    yaw in [-180,180] -> u in [0,1]
    pitch in [-90,90] -> v in [0,1]  (or [-180,180] if stretch_pitch_to_180=True)
    """
    yaw_deg   = np.asarray(yaw_deg, dtype=float)
    pitch_deg = np.asarray(pitch_deg, dtype=float)

    u = (yaw_deg + 180.0) / 360.0
    if stretch_pitch_to_180:
        v = (pitch_deg + 180.0) / 360.0
    else:
        v = (pitch_deg + 90.0) / 180.0
    return np.stack([u, v], axis=-1)


