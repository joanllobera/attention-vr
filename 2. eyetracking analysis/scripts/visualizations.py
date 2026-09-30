import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import LogFormatter, ScalarFormatter
import matplotlib.patches as patches
# Optional for KDE mode
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib as mpl
import matplotlib.image as mpimg
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm
from scipy import stats


def plot_eye_displacement_baseline_vs_overlay(
    df_track,
    *,
    eye: str = "Right",
    baseline: str = "Valid",
    overlay: str = "Test",
    xlim=(-180, 180),
    ylim=(-180, 180),
    gridsize_hex: int = 80,
    bins_global: int = 100,
    vmax_percentile: float = 95.0,
    jitter: float = 0.0,
    overlay_color: str = "red",
    overlay_size: int = 10,
    overlay_alpha: float = 0.5,
    cmap: str = "viridis",
    figsize=(7,7),
    title: str | None = None,
    savepath: str | None = None,
    show: bool = True,
):
    """
    Plot baseline condition as hexbin (density) and overlay condition as scatter points.
    """

    # --- choose columns ---
    eye = eye.capitalize()
    if eye not in ("Left", "Right"):
        raise ValueError("eye must be 'Left' or 'Right'")
    yaw_col   = "rEyeYaw" if eye == "Right" else "lEyeYaw"
    pitch_col = "rEyePitch" if eye == "Right" else "lEyePitch"

    # --- baseline subset ---
    base = df_track[df_track["condition"] == baseline]
    yaw_base = base[yaw_col].to_numpy()
    pit_base = base[pitch_col].to_numpy()
    m = np.isfinite(yaw_base) & np.isfinite(pit_base)
    Xb, Yb = yaw_base[m], pit_base[m]

    # --- overlay subset ---
    over = df_track[df_track["condition"] == overlay]
    yaw_over = over[yaw_col].to_numpy()
    pit_over = over[pitch_col].to_numpy()
    m = np.isfinite(yaw_over) & np.isfinite(pit_over)
    Xo, Yo = yaw_over[m], pit_over[m]

    if jitter > 0:
        Xb = Xb + np.random.uniform(-jitter, jitter, size=Xb.size)
        Yb = Yb + np.random.uniform(-jitter, jitter, size=Yb.size)
        Xo = Xo + np.random.uniform(-jitter, jitter, size=Xo.size)
        Yo = Yo + np.random.uniform(-jitter, jitter, size=Yo.size)

    # --- compute global norm for hexbin ---
    H, *_ = np.histogram2d(Xb, Yb, bins=bins_global, range=[list(xlim), list(ylim)])
    Hnz = H[H > 0]
    if Hnz.size == 0:
        vmin, vmax = 1, 1
    else:
        vmin = max(1, Hnz.min())
        vmax = np.percentile(Hnz, vmax_percentile)
    norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)

    # --- plot ---
    fig, ax = plt.subplots(figsize=figsize)

    if Xb.size > 0:
        ax.hexbin(
            Xb, Yb,
            gridsize=gridsize_hex,
            extent=(xlim[0], xlim[1], ylim[0], ylim[1]),
            mincnt=1,
            cmap=cmap,
            norm=norm
        )
    if Xo.size > 0:
        ax.scatter(
            Xo, Yo,
            s=overlay_size,
            c=overlay_color,
            alpha=overlay_alpha,
            label=overlay
        )

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Yaw (deg)")
    ax.set_ylabel("Pitch (deg)")
    ax.set_title(title or f"{eye} eye: {baseline} vs {overlay}")

    if Xo.size > 0:
        ax.legend(loc="upper right")

    # colorbar for hexbin
    if Xb.size > 0:
        cbar = fig.colorbar(ax.collections[0], ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("log(counts)")

    fig.tight_layout()
    if savepath:
        fig.savefig(savepath, dpi=300, bbox_inches="tight")
    if show:
        plt.show()

    return fig, ax

def plot_eye_displacement_by_distractors(
    df_track,
    *,
    eye: str = "Left",                       # "Left" or "Right"
    condition=("Valid",),                    # tuple/list of conditions to include (default: only "Valid")
    lateralisation=("Left", "Right"),
    position=("Front", "Rear"),
    nb_dist=("Zero", "One_near", "One_far", "Three"),
    pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],
    bins_global: int = 50,                   # bins for global 2D histogram (LogNorm scaling)
    gridsize_hex: int = 50,                  # hexbin grid size
    xlim=(-180, 180),
    ylim=(-90, 90),
    figsize=(10, 10),
    cmap="plasma",
    merge_left_right=True,
    log_scale: float = 1.0,                  # factor to reduce vmax in LogNorm (default 1.0 = no change)
    savepath: str | None = None,             # e.g., "eye_displacement_plot_Valid.jpg"
    show: bool = True
):
    """
    Create a 4x4 hexbin grid of eye yaw/pitch distributions across lateralisation, position, and nb_dist,
    using a global LogNorm so all subplots share the same color scale.

    Returns
    -------
    fig, axes, mapping
        fig, axes from matplotlib, and a dict mapping "(lat, pos, dist)" -> subplot index.
    """
    # Build legend handles once
    legend_handles = []
        
    # Add handle for pilars and main pilar
    legend_handles.extend(
        [Line2D([0], [0], color='gray', lw=1, linestyle='--', label='Pilars'),
        Line2D([0], [0], color='gray', lw=2, linestyle='--', label='Pilar of Interest')]
    )

    # Special case: if condition is "Test", just plot one heatmap
    if condition == "Test" or (isinstance(condition, (tuple, list)) and condition == ("Test",)):
        df_comb = df_track[df_track["condition"] == "Test"]
        if not df_comb.empty:
            if eye == "Right":
                yaw_deg = df_comb["rEyeYaw"].to_numpy()
                pitch_deg = df_comb["rEyePitch"].to_numpy()
            else:
                yaw_deg = df_comb["lEyeYaw"].to_numpy()
                pitch_deg = df_comb["lEyePitch"].to_numpy()


            

            m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
            x, y = yaw_deg[m], pitch_deg[m]

            if x.size > 0:
                # compute counts to set a good LogNorm range
                H, xe, ye = np.histogram2d(x, y, bins=bins_global, range=[list(xlim), list(ylim)])
                if (H > 0).any():
                    vmin = H[H > 0].min()   # smallest nonzero count
                    vmax = H.max()
                else:
                    vmin, vmax = 1, 1
                norm = mcolors.LogNorm(vmin=vmin, vmax=vmax/log_scale)

                fig, ax = plt.subplots(figsize=(6, 6))
                hb = ax.hexbin(
                    x, y,
                    gridsize=gridsize_hex,    # try 80–120 if everything still looks flat
                    extent=(xlim[0], xlim[1], ylim[0], ylim[1]),
                    mincnt=1,                 # ignore empty bins
                    cmap="viridis",
                    norm=norm
                )
                ax.set_xlim(*xlim); ax.set_ylim(*ylim)
                ax.set_xlabel("Yaw (deg)"); ax.set_ylabel("Pitch (deg)")
                ax.set_title(f"Test: n={x.size}")
                if show:
                    plt.show()
                return fig, ax
    else:
    
        # ---------------- Validate inputs ----------------
        eye = eye.capitalize()
        if eye not in ("Left", "Right"):
            raise ValueError("eye must be 'Left' or 'Right'")

        # Columns required
        required_cols = {
            "lateralisation", "position", "condition", "nb_dist",
            "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
        }
        missing = required_cols - set(df_track.columns)
        if missing:
            raise ValueError(f"Missing required columns in df_track: {missing}")
        # ---------------- Prepare figure/grid ----------------
        if len(lateralisation) != 2 or len(position) != 2 or len(nb_dist) != 4:
            raise ValueError("This layout expects 2 lateralisation, 2 position, and 4 nb_dist categories.")

        # Columns depend on merge flag
        if merge_left_right:
            # collapse Left/Right into 2 columns (Front, Rear)
            n_rows, n_cols = 4, 2
            col_map = {
                f"{lateralisation[0]} {position[0]}": 0,
                f"{lateralisation[1]} {position[0]}": 0,
                f"{lateralisation[0]} {position[1]}": 1,
                f"{lateralisation[1]} {position[1]}": 1,
            }
        else:
            n_rows, n_cols = 4, 4
            col_map = {
                f"{lateralisation[0]} {position[0]}": 0,
                f"{lateralisation[0]} {position[1]}": 1,
                f"{lateralisation[1]} {position[0]}": 2,
                f"{lateralisation[1]} {position[1]}": 3,
            }

        if merge_left_right:
            column_labels = [f"L+R {position[0]}", f"L+R {position[1]}"]
        else:
            column_labels = [
                f"{lateralisation[0]} {position[0]}",
                f"{lateralisation[0]} {position[1]}",
                f"{lateralisation[1]} {position[0]}",
                f"{lateralisation[1]} {position[1]}",
            ]

        row_map = {nb_dist[i]: i for i in range(4)}

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
        axes = axes.flatten()

        # ---------------- Global scaling (LogNorm) ----------------
        if eye == "Right":
            valid_mask = np.isfinite(df_track["rEyeYaw"]) & np.isfinite(df_track["rEyePitch"])
            yaw_all = df_track.loc[valid_mask, "rEyeYaw"].to_numpy()
            pitch_all = df_track.loc[valid_mask, "rEyePitch"].to_numpy()
        else:
            valid_mask = np.isfinite(df_track["lEyeYaw"]) & np.isfinite(df_track["lEyePitch"])
            yaw_all = df_track.loc[valid_mask, "lEyeYaw"].to_numpy()
            pitch_all = df_track.loc[valid_mask, "lEyePitch"].to_numpy()
        if merge_left_right:
            lat_all = df_track.loc[valid_mask, "lateralisation"].to_numpy()
            yaw_all = yaw_all.copy()
            yaw_all[lat_all == lateralisation[0]] *= -1

        hb_all = np.histogram2d(yaw_all, pitch_all, bins=bins_global,
                                range=[list(xlim), list(ylim)])
        counts = hb_all[0]
        vmin = np.min(counts[counts > 0]) if np.any(counts > 0) else 1
        vmax = np.max(counts) if counts.size else 1
        norm = mcolors.LogNorm(vmin=vmin, vmax=vmax/log_scale)

        # ---------------- Plot per combination ----------------
        mapping = {}
        hb_last = None

        # force condition into a tuple/list
        if isinstance(condition, str):
            condition_iter = (condition,)
        else:
            condition_iter = tuple(condition)

        for dist in nb_dist:
            for pos in position:
                row_idx = row_map[dist]

                if merge_left_right:
                    # une seule colonne par position
                    col_idx = col_map[f"{lateralisation[0]} {pos}"]
                    subplot_idx = row_idx * n_cols + col_idx
                    ax = axes[subplot_idx]

                    # on prend les deux latéralisations d'un coup
                    df_comb = df_track[
                        (df_track["position"] == pos) &
                        (df_track["nb_dist"] == dist) &
                        (df_track["condition"].isin(condition_iter))
                    ]
                    if not df_comb.empty:
                        if eye == "Right":
                            yaw_deg = df_comb["rEyeYaw"].to_numpy()
                            pitch_deg = df_comb["rEyePitch"].to_numpy()
                        else:
                            yaw_deg = df_comb["lEyeYaw"].to_numpy()
                            pitch_deg = df_comb["lEyePitch"].to_numpy()

                        lat_vals = df_comb["lateralisation"].to_numpy()

                        m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
                        x = yaw_deg[m]
                        y = pitch_deg[m]
                        lat_m = lat_vals[m]

                        # miroir pour la latéralisation "Left" (lateralisation[0])
                        x[lat_m == lateralisation[0]] *= -1

                        if x.size > 0:
                            hb_last = ax.hexbin(
                                x, y,
                                gridsize=gridsize_hex,
                                cmap=plt.get_cmap(cmap),
                                norm=norm,
                                mincnt=1,
                                extent=(xlim[0], xlim[1], ylim[0], ylim[1]),
                            )
                            ax.set_title(f"nb data = {len(x)}", fontsize=10)
                        else:
                            ax.set_title("nb data = 0", fontsize=10)

                        ax.set_xlim(*xlim)
                        ax.set_ylim(*ylim)

                        # lignes des pilars (à adapter à ton goût pour le mode merge)
                        for angle in pilars_angle:
                            ax.axvline(x=angle, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                                                # Add vertical lines for pilars
                        if pos == position[0]:
                            ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=2, alpha=0.9)
                        elif pos == position[1]:
                            ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=2, alpha=0.9)

                        else:
                            ax.set_title("nb data = 0", fontsize=10)
                            ax.set_xlim(*xlim)
                            ax.set_ylim(*ylim)

                        mapping[(f"{lateralisation[0]}+{lateralisation[1]}", pos, dist)] = subplot_idx
                else:
                    # ancien comportement : une subplot par latéralisation
                    for lat in lateralisation:
                        col_idx = col_map[f"{lat} {pos}"]
                        subplot_idx = row_idx * n_cols + col_idx
                        ax = axes[subplot_idx]

                        df_comb = df_track[
                            (df_track["lateralisation"] == lat) &
                            (df_track["position"] == pos) &
                            (df_track["nb_dist"] == dist) &
                            (df_track["condition"].isin(condition_iter))
                        ]

                        if not df_comb.empty:
                            if eye == "Right":
                                yaw_deg = df_comb["rEyeYaw"].to_numpy()
                                pitch_deg = df_comb["rEyePitch"].to_numpy()
                            else:
                                yaw_deg = df_comb["lEyeYaw"].to_numpy()
                                pitch_deg = df_comb["lEyePitch"].to_numpy()

                            m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
                            x = yaw_deg[m]
                            y = pitch_deg[m]

                            if x.size > 0:
                                hb_last = ax.hexbin(
                                    x, y,
                                    gridsize=gridsize_hex,
                                    cmap=plt.get_cmap(cmap),
                                    norm=norm,
                                    mincnt=1,
                                    extent=(xlim[0], xlim[1], ylim[0], ylim[1]),
                                )
                                ax.set_title(f"nb data = {len(x)}", fontsize=10)
                            else:
                                ax.set_title("nb data = 0", fontsize=10)

                            ax.set_xlim(*xlim)
                            ax.set_ylim(*ylim)

                            # Add vertical lines for pilars
                            for angle in pilars_angle:
                                ax.axvline(x=angle, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                            if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                                ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=2, alpha=0.9)
                            elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                                ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=2, alpha=0.9)
                            elif lat == lateralisation[1] and pos == position[0]:
                                ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=2, alpha=0.9)
                            elif lat == lateralisation[1] and pos == position[1]:
                                ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=2, alpha=0.9)

                        else:
                            ax.set_title("nb data = 0", fontsize=10)
                            ax.set_xlim(*xlim)
                            ax.set_ylim(*ylim)

                        mapping[(lat, pos, dist)] = subplot_idx

        # ---------------- Axis labels ----------------
        for i, ax in enumerate(axes):
            r, c = divmod(i, n_cols)
            if r == n_rows - 1:
                ax.set_xlabel("Yaw [deg]")
            if c == 0:
                ax.set_ylabel("Pitch [deg]")

        # ---------------- Colorbar ----------------
        cax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
        if hb_last is not None:
            cb = fig.colorbar(hb_last, cax=cax)
            cb.set_label("log10(counts)")
            cb.formatter = LogFormatter(10)
            #cb.update_normal()

        # ---------------- Titles for columns/rows ----------------
        row_titles = ["Zero", "One\nNear", "One\nFar", "Three"]
        for j, title in enumerate(row_titles):
            fig.text(0.01, 0.80 - j * 0.23, title, ha="center", fontsize=14, fontweight="normal")

        for i, title in enumerate(column_labels):
            fig.text(
                0.22 + i * (0.5 if merge_left_right else 0.185),
                0.95,
                title,
                ha="center",
                fontsize=14,
                fontweight="bold"
            )

        condition_str = " ".join(condition_iter)
        fig.suptitle(
            f"Eye Displacement during Trials (Yaw/Pitch) ({condition_str} Trials)",
            fontsize=16, y=1.02
        )

        fig.legend(handles=legend_handles, title="Legend", loc="upper center", ncol=len(legend_handles), bbox_to_anchor=(0.5, 0.98))

        plt.subplots_adjust(left=0.15, right=0.85, top=0.90, bottom=0.05, hspace=0.3, wspace=0.2)

        # ---------------- Save/Show ----------------
        if savepath:
            fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
        if show:
            plt.show()

        return fig, axes, mapping

def plot_eye_displacement_by_distractors_violin(
    df_track,
    *,
    eye: str = "Left",                       # "Left" or "Right"
    condition=("Valid",),                    # tuple/list of conditions to include (default: only "Valid")
    lateralisation=("Left", "Right"),
    position=("Front", "Rear"),
    nb_dist=("Zero", "One_near", "One_far", "Three"),
    pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],
    bins_global: int = 50,                   # bins for global 2D histogram (LogNorm scaling)
    gridsize_hex: int = 50,                  # hexbin grid size
    xlim=(-270, 270),
    figsize=(10, 10),
    cmap="plasma",
    merge_left_right=True,
    log_scale: float = 1.0,                  # factor to reduce vmax in LogNorm (default 1.0 = no change)
    savepath: str | None = None,             # e.g., "eye_displacement_plot_Valid.jpg"
    show: bool = True
):
    """
    Create a 4x4 hexbin grid of eye yaw/pitch distributions across lateralisation, position, and nb_dist,
    using a global LogNorm so all subplots share the same color scale.

    Returns
    -------
    fig, axes, mapping
        fig, axes from matplotlib, and a dict mapping "(lat, pos, dist)" -> subplot index.
    """
    # Build legend handles once
    legend_handles = []
    # Add handle for pilars and main pilar
    legend_handles.extend(
        [Line2D([0], [0], color='gray', lw=1, linestyle='--', label='Pilars'),
        Line2D([0], [0], color='gray', lw=2, linestyle='--', label='Pilar of Interest')]
    )

    # ---------------- Validate inputs ----------------
    eye = eye.capitalize()
    if eye not in ("Left", "Right"):
        raise ValueError("eye must be 'Left' or 'Right'")

    # Columns required
    required_cols = {
        "lateralisation", "position", "condition", "nb_dist",
        "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
    }
    missing = required_cols - set(df_track.columns)
    if missing:
        raise ValueError(f"Missing required columns in df_track: {missing}")

    # ---------------- Prepare figure/grid ----------------
    if len(lateralisation) != 2 or len(position) != 2 or len(nb_dist) != 4:
        raise ValueError("This layout expects 2 lateralisation, 2 position, and 4 nb_dist categories.")

    # Columns depend on merge flag
    if merge_left_right:
        # collapse Left/Right into 2 columns (Front, Rear)
        n_rows, n_cols = 1, 2
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 0,
            f"{lateralisation[0]} {position[1]}": 1,
            f"{lateralisation[1]} {position[1]}": 1,
        }
    else:
        n_rows, n_cols = 1, 4
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[0]} {position[1]}": 1,
            f"{lateralisation[1]} {position[0]}": 2,
            f"{lateralisation[1]} {position[1]}": 3,
        }

    row_map = {nb_dist[i]: i for i in range(4)}

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
    axes = axes.flatten()

    # ---------------- Global scaling (LogNorm) ----------------
    if eye == "Right":
        valid_mask = np.isfinite(df_track["rEyeYaw"]) & np.isfinite(df_track["rEyePitch"])
        yaw_all = df_track.loc[valid_mask, "rEyeYaw"].to_numpy()
        pitch_all = df_track.loc[valid_mask, "rEyePitch"].to_numpy()
    else:
        valid_mask = np.isfinite(df_track["lEyeYaw"]) & np.isfinite(df_track["lEyePitch"])
        yaw_all = df_track.loc[valid_mask, "lEyeYaw"].to_numpy()
        pitch_all = df_track.loc[valid_mask, "lEyePitch"].to_numpy()


    # ---------------- Plot per combination ----------------
    mapping = {}
    hb_last = None

    # force condition into a tuple/list
    if isinstance(condition, str):
        condition_iter = (condition,)
    else:
        condition_iter = tuple(condition)
    for pos in position: 
        data_per_plot = [[] for _ in range(4)] # init list for each nb_dist
        for lat in lateralisation:
            if not(merge_left_right): data_per_plot = [[] for _ in range(4)] # init list for each nb_dist
            for dist in nb_dist:
                row_idx = row_map[dist]
                col_idx = col_map[f"{lat} {pos}"]
                subplot_idx = col_idx
                ax = axes[subplot_idx]

                # Set ax lim
                ax.set_xlim([xlim[0], xlim[1]])
                ticks = np.arange(start=xlim[0],stop=xlim[1]+0.01,step=90)
                ax.set_xticks(ticks)

                # Filter rows for this combination (any of the selected conditions)
                df_comb = df_track[
                    (df_track["lateralisation"] == lat) &
                    (df_track["position"] == pos) &
                    (df_track["nb_dist"] == dist) &
                    (df_track["condition"].isin(condition_iter))
                ]


                if eye == "Right":
                    yaw_deg = df_comb["rEyeYaw"].to_numpy()
                    pitch_deg = df_comb["rEyePitch"].to_numpy()
                else:
                    yaw_deg = df_comb["lEyeYaw"].to_numpy()
                    pitch_deg = df_comb["lEyePitch"].to_numpy()

                m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
                x = yaw_deg[m]
                # If we merge sides, mirror Left yaw so "toward the target" has the same sign
                if merge_left_right and lat == lateralisation[0]:
                    x = -x
            
                
                # Accumulate data for violin plot
                data_per_plot[row_idx] = np.append(data_per_plot[row_idx],x)
                
            # Add vertical lines for pilars
            for angle in pilars_angle:
                ax.axvline(x=angle, color='gray', linestyle='--', linewidth=1, alpha=0.7)
            if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[1] and pos == position[0]:
                ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[1] and pos == position[1]:
                ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)


            if merge_left_right and lat == lateralisation[-1]: ax.violinplot(data_per_plot, orientation='horizontal', positions=[0,-1,-2,-3], widths=0.7)
            elif not(merge_left_right): ax.violinplot(data_per_plot, orientation='horizontal')
            ax.set_xlim(*xlim)
            ax.get_yaxis().set_visible(False)

    # ---------------- Titles for columns/rows ----------------
    row_titles = ["0 Distractor", "1 Distractor\nNear", "1 Distractor\nFar", "3 Distractors"]
    for j, title in enumerate(row_titles):
        fig.text(0.01, 0.80 - j * 0.23, title, ha="center", fontsize=14, fontweight="bold")

    if merge_left_right:
        # two columns: Front, Rear
        merged_titles = (position[0], position[1])  # ("Front", "Rear")
        x_positions = (0.32, 0.68)                  # tweak if needed
        for x, title in zip(x_positions, merged_titles):
            fig.text(x, 0.95, title, ha="center", fontsize=14, fontweight="bold")
    else:
        col_titles = list(col_map.keys())
        for i, title in enumerate(col_titles):
            fig.text(0.22 + i * 0.185, 0.95, title, ha="center", fontsize=14, fontweight="bold")

    condition_str = " ".join(condition_iter)
    fig.suptitle(
        f"Eye Displacement during Trials (Yaw/Pitch) ({condition_str} Trials)",
        fontsize=16, y=1.02
    )

    fig.legend(handles=legend_handles, title="Legend", loc="upper center", ncol=len(legend_handles), bbox_to_anchor=(0.5, 0.98))

    plt.subplots_adjust(left=0.15, right=0.85, top=0.90, bottom=0.05, hspace=0.3, wspace=0.2)

    # ---------------- Save/Show ----------------
    if savepath:
        fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
    if show:
        plt.show()

    return fig, axes, mapping

def plot_eye_at_trial_end(
        df_track,
        df_step,
        *,
        tolerance: float = 0.01,                 # seconds tolerance to match end times
        eye: str = "Left",                       # "Left" or "Right"
        condition=("Valid",),                    # tuple/list or single string
        lateralisation=("Left", "Right"),
        position=("Front", "Rear"),
        nb_dist=("Zero", "One_near", "One_far", "Three"),
        pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],
        mode: str = "kde",                       # "kde" (seaborn) or "hexbin"
        # KDE params
        kde_levels: int = 100,
        kde_fill: bool = True,
        kde_thresh: float = 0.1,
        kde_cmap: str = "rocket",
        # Hexbin params
        gridsize_hex: int = 50,
        bins_global: int = 50,
        cmap_hex: str = "plasma",
        # Plot framing / I/O
        xlim=(-180, 180),
        ylim=(-90, 90),
        figsize=(10, 10),
        # LogNorm scaling factor (for hexbin mode only)
        log_scale: float = 1.0,                  # factor to reduce vmax in Log
        savepath: str | None = None,
        show: bool = True,
    ):
    """
    Extract eye samples near trial end times and plot yaw/pitch by lateralisation, position, and nb_dist.

    Returns
    -------
    fig, axes, mapping, df_target
        fig/axes: Matplotlib figure and axes array
        mapping: dict {(lat, pos, dist) -> subplot_index}
        df_target: filtered dataframe of track rows near end times
    """
    # Special case: if condition is "Test", just plot one heatmap
    if condition == "Test" or (isinstance(condition, (tuple, list)) and condition == ("Test",)):
        df_comb = df_track[df_track["condition"] == "Test"]
        if not df_comb.empty:
            if eye == "Right":
                yaw_deg = df_comb["rEyeYaw"].to_numpy()
                pitch_deg = df_comb["rEyePitch"].to_numpy()
            else:
                yaw_deg = df_comb["lEyeYaw"].to_numpy()
                pitch_deg = df_comb["lEyePitch"].to_numpy()
            
            fig, ax = plt.subplots(figsize=(6,6))

            m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
            x, y = yaw_deg[m], pitch_deg[m]

            if x.size > 0:
                if mode.lower() == "hexbin":
                    hb_last = ax.hexbin(
                        x, y,
                        gridsize=gridsize_hex,
                        cmap=plt.get_cmap(cmap_hex),
                        norm=norm,
                        mincnt=1
                    )
                elif mode.lower() == "kde":
                    sns.kdeplot(
                        x=x, y=y, ax=ax,
                        fill=kde_fill,
                        levels=kde_levels,
                        alpha=1,
                        thresh=kde_thresh,
                        cmap=kde_cmap
                    )
                else:
                    raise ValueError("mode must be 'kde' or 'hexbin'")
                ax.set_xlim(*xlim); ax.set_ylim(*ylim)
                ax.set_xlabel("Yaw (deg)"); ax.set_ylabel("Pitch (deg)")
                ax.set_title("Test condition")
                if show:
                    plt.show()
                return fig, ax
    else:
        
        # ----------- Validate inputs & columns -----------
        eye = eye.capitalize()
        if eye not in ("Left", "Right"):
            raise ValueError("eye must be 'Left' or 'Right'")

        if isinstance(condition, str):
            condition_iter = (condition,)
        else:
            condition_iter = tuple(condition)

        required_track_cols = {
            "timeSinceStartup", "lateralisation", "position", "condition", "nb_dist",
            "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
        }
        missing_track = required_track_cols - set(df_track.columns)
        if missing_track:
            raise ValueError(f"Missing columns in df_track: {missing_track}")

        required_step_cols = {"endTime"}
        missing_step = required_step_cols - set(df_step.columns)
        if missing_step:
            raise ValueError(f"Missing columns in df_step: {missing_step}")

        # ----------- Extract target samples near end times -----------
        track_times = df_track["timeSinceStartup"].to_numpy()
        end_times = df_step["endTime"].to_numpy()

        # ----------- Extract target samples near end times -----------
        # Build mapping of endTime per trial
        df_end = (df_step.loc[df_step['endTime'].notna(), ['trial','endTime']]
                        .sort_values(['trial','endTime'])
                        .drop_duplicates('trial', keep='last'))

        # Merge first, then filter on the merged frame to keep index alignment
        dfm = df_track.merge(df_end, on='trial', how='inner')
        dfm = dfm.loc[np.isfinite(dfm['timeSinceStartup'])].copy()
        dfm['abs_dt'] = (dfm['timeSinceStartup'] - dfm['endTime']).abs()

        # nearest sample per trial
        idx_near = dfm.groupby('trial')['abs_dt'].idxmin()
        near = dfm.loc[idx_near]

        # keep the nearest only if within tolerance
        picked = near[near['abs_dt'] <= tolerance].copy()

        # fallback for trials without a within-tolerance point:
        missing = set(near.loc[near['abs_dt'] > tolerance, 'trial'])
        if missing:
            sub = dfm[dfm['trial'].isin(missing)].copy()
            # prefer last ≤ endTime; else last overall
            sub['at_or_before'] = sub['timeSinceStartup'] <= sub['endTime']
            def _pick(g):
                g0 = g[g['at_or_before']]
                return g0.loc[g0['timeSinceStartup'].idxmax()] if not g0.empty else g.loc[g['timeSinceStartup'].idxmax()]
            fb = pd.DataFrame([_pick(g) for _, g in sub.groupby('trial')])
            picked = pd.concat([picked, fb], ignore_index=True)

        # one row per trial
        df_target = (picked.sort_values(['trial','timeSinceStartup'])
                            .drop_duplicates('trial', keep='last'))

        # ----------- Prepare figure/grid -----------
        if len(lateralisation) != 2 or len(position) != 2 or len(nb_dist) != 4:
            raise ValueError("Layout expects 2 lateralisation, 2 position, and 4 nb_dist categories.")

        n_rows, n_cols = 4, 4
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
        axes = axes.flatten()

        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 1,
            f"{lateralisation[0]} {position[1]}": 2,
            f"{lateralisation[1]} {position[1]}": 3,
        }
        row_map = {nb_dist[i]: i for i in range(4)}

        # ----------- Global scaling for hexbin (LogNorm) -----------
        hb_last = None
        if mode.lower() == "hexbin":
            if eye == "Right":
                valid_mask = np.isfinite(df_target["rEyeYaw"]) & np.isfinite(df_target["rEyePitch"])
                yaw_all = df_target.loc[valid_mask, "rEyeYaw"].to_numpy()
                pitch_all = df_target.loc[valid_mask, "rEyePitch"].to_numpy()
            else:
                valid_mask = np.isfinite(df_target["lEyeYaw"]) & np.isfinite(df_target["lEyePitch"])
                yaw_all = df_target.loc[valid_mask, "lEyeYaw"].to_numpy()
                pitch_all = df_target.loc[valid_mask, "lEyePitch"].to_numpy()

            hb_all = np.histogram2d(yaw_all, pitch_all, bins=bins_global,
                                    range=[list(xlim), list(ylim)])
            counts = hb_all[0]
            vmin = np.min(counts[counts > 0]) if np.any(counts > 0) else 1
            vmax = np.max(counts) if counts.size else 1
            norm = mcolors.LogNorm(vmin=vmin, vmax=vmax/log_scale)
        else:
            norm = None  # Not used in KDE mode

        # ----------- Plot loops -----------
        mapping = {}

        for lat in lateralisation:
            for pos in position:
                for dist in nb_dist:
                    row_idx = row_map[dist]
                    col_idx = col_map[f"{lat} {pos}"]
                    subplot_idx = row_idx * n_cols + col_idx
                    ax = axes[subplot_idx]

                    df_comb = df_target[
                        (df_target["lateralisation"] == lat) &
                        (df_target["position"] == pos) &
                        (df_target["nb_dist"] == dist) &
                        (df_target["condition"].isin(condition_iter))
                    ]

                    if not df_comb.empty:
                        if eye == "Right":
                            yaw_deg = df_comb["rEyeYaw"].to_numpy()
                            pitch_deg = df_comb["rEyePitch"].to_numpy()
                        else:
                            yaw_deg = df_comb["lEyeYaw"].to_numpy()
                            pitch_deg = df_comb["lEyePitch"].to_numpy()

                        m = np.isfinite(yaw_deg) & np.isfinite(pitch_deg)
                        x, y = yaw_deg[m], pitch_deg[m]

                        if x.size > 1:
                            if mode.lower() == "hexbin":
                                hb_last = ax.hexbin(
                                    x, y,
                                    gridsize=gridsize_hex,
                                    cmap=plt.get_cmap(cmap_hex),
                                    norm=norm,
                                    mincnt=1
                                )
                            elif mode.lower() == "kde":
                                sns.kdeplot(
                                    x=x, y=y, ax=ax,
                                    fill=kde_fill,
                                    levels=kde_levels,
                                    alpha=1,
                                    thresh=kde_thresh,
                                    cmap=kde_cmap
                                )
                            else:
                                raise ValueError("mode must be 'kde' or 'hexbin'")
                            ax.set_title(f"Nb data: {len(x)}", fontsize=10)
                        else:
                            ax.set_title("Nb data: 0", fontsize=10)
                    else:
                        ax.set_title("Nb data: 0", fontsize=10)

                    ax.set_xlim(*xlim)
                    ax.set_ylim(*ylim)
                    mapping[(lat, pos, dist)] = subplot_idx

        # ----------- Axis labels -----------
        for i, ax in enumerate(axes):
            r, c = divmod(i, n_cols)
            if r == n_rows - 1:
                ax.set_xlabel("Yaw [deg]")
            if c == 0:
                ax.set_ylabel("Pitch [deg]")

        # ----------- Colorbar (hexbin only) -----------
        if mode.lower() == "hexbin" and hb_last is not None:
            cax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
            cb = fig.colorbar(hb_last, cax=cax)
            cb.set_label("log10(counts)")
            cb.formatter = LogFormatter(10)
            cb.update_normal()

        # ----------- Titles -----------
        row_titles = ["0 Distractor", "1 Distractor\nNear", "1 Distractor\nFar", "3 Distractors"]
        for i, title in enumerate(row_titles):
            fig.text(0.01, 0.80 - i * 0.23, title, ha="center", fontsize=14, fontweight="bold")

        col_titles = col_map.keys()
        for j, title in enumerate(col_titles):
            fig.text(0.22 + j * 0.185, 0.95, title, ha="center", fontsize=14, fontweight="bold")

        condition_str = " ".join(condition_iter)
        fig.suptitle(
            f"Eye position when target acquired (Yaw/Pitch) ({condition_str} Trials)",
            fontsize=16, y=1.02
        )
        plt.subplots_adjust(left=0.15, right=0.85, top=0.90, bottom=0.05, hspace=0.3, wspace=0.2)

        # ----------- Save/Show -----------
        if savepath:
            fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
        if show:
            plt.show()

        return fig, axes, mapping, df_target

def plot_dwell_time(df_trials, angle_roi, savefig="fig/dwell_time_boxplots.png"):
    # Config
    dwell_cols = ["Interest_dwell_time", "Third_dwell_time", "Far_dwell_time", "Near_dwell_time"]
    dwell_labels = ["Interest", "Third", "Far", "Near"]
    distractors = ['Zero', 'One_near','One_far', 'Three']
    positions   = ["Front", "Rear"] 

    fig, axes = plt.subplots(4, 2, figsize=(10, 12), sharey=True)
    axes = np.atleast_2d(axes)

    for i, d in enumerate(distractors[:4]):        # 4 rows (one per distractor level)
        for j, pos in enumerate(positions[:2]):    # 2 columns (positions)
            ax = axes[i, j]
            sub = df_trials[(df_trials["nb_dist"] == d) & (df_trials["position"] == pos)]

            # Collect data arrays for the 4 dwell metrics (drop NaNs)
            data = [sub[col].dropna().values for col in dwell_cols]

            # Boxplot
            #ax.boxplot(data, tick_labels=dwell_labels, showfliers=False)
            ax.boxplot(data, labels=dwell_labels, showfliers=False)
            ax.set_title(f"{pos} • {d}")
            if j == 0:
                ax.set_ylabel("Dwell time (s)")
            ax.tick_params(axis="x", labelrotation=0)

    fig.suptitle("Dwell time on ROIs", y=0.995)
    fig.text(s=f"Angle around ROIs : {angle_roi}°",x=0.5, y=0.97, horizontalalignment='center', fontsize=8)
    fig.tight_layout()
    if savefig: plt.savefig(savefig, dpi=300)
    plt.show()

def plot_temporal_y_rotation_condition(
    
    df_track,
    *,
    eye: str = "Left",                       # "Left" or "Right"
    condition=("Valid",),                    # tuple/list of conditions to include (default: only "Valid")
    lateralisation=("Left", "Right"),
    position=("Front", "Rear"),
    nb_dist=("Zero", "One_near", "One_far", "Three"),
    pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],               # angle of the pilars in degrees (0 = facing participant)   
    figsize=(16, 9),
    colors=["Green", "Red"],
    median_colors=["lightgreen", "lightcoral"],
    alpha: float = 0.3,    
    v_lim: tuple = (-180, 180),
    t_lim: tuple = (0, 3),
    dt = 0.01,
    merge_left_right=False,                    
    savepath: str | None = None,             # e.g., "eye_displacement_plot_Valid.jpg"
    show: bool = True
):
    """
    Create a 4 subplot of rotation Y (y axis) over time across lateralisation and position

    Returns
    -------
    fig, axes
        fig, axes from matplotlib
    """
    # Build legend handles once
    legend_handles = []

    # Add handles for raw trial lines
    legend_handles.extend([
        Line2D([0], [0], color=colors[i], lw=1, alpha=0.5, label=f"{cond} trials")
        for i, cond in enumerate(condition)
    ])

    # Add handle for pilars and main pilar
    legend_handles.extend(
        [Line2D([0], [0], color='gray', lw=1, linestyle='--', label='Pilars'),
        Line2D([0], [0], color='gray', lw=2, linestyle='--', label='Pilar of Interest')]
    )




    # ---------------- Validate inputs ----------------
    eye = eye.capitalize()
    if eye not in ("Left", "Right"):
        raise ValueError("eye must be 'Left' or 'Right'")

    # Columns required
    required_cols = {
        "lateralisation", "position", "condition", "nb_dist",
        "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
    }
    missing = required_cols - set(df_track.columns)
    if missing:
        raise ValueError(f"Missing required columns in df_track: {missing}")

    # ---------------- Prepare figure/grid ----------------
    if merge_left_right:
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 0,
            f"{lateralisation[0]} {position[1]}": 1,
            f"{lateralisation[1]} {position[1]}": 1,
        }
        n_rows, n_cols = 1, 2
    else:
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 1,
            f"{lateralisation[0]} {position[1]}": 2,
            f"{lateralisation[1]} {position[1]}": 3,
        }
        n_rows, n_cols = 1, 4
    

    

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
    axes = axes.flatten()

    

    # ---------------- Plot per combination ---------------
    
    
    for pos in position:
        active_trials_per_time_per_plot = []; nb_data = 0
        for lat in lateralisation:
            if not(merge_left_right): active_trials_per_time_per_plot = []; nb_data = 0
            for i, condi in enumerate(condition):

                ###### for each subplot

                color = colors[i]
                median_color = median_colors[i]
                ax = axes[col_map[f"{lat} {pos}"]]
                if merge_left_right:
                    ax.set_title(f"{pos}")
                else:
                    ax.set_title(f"{lat} {pos}")
                
                yaw_trials = []
                    
                df_comb = df_track[
                    (df_track["lateralisation"] == lat) &
                    (df_track["position"] == pos) &
                    (df_track["condition"] == condi)
                ].copy()
                trials = df_comb["trial"].unique()

                nb_data += len(trials)


                for trial in trials:
                    df_trial = df_comb[df_comb["trial"] == trial].copy()
                    df_trial.sort_values("timeSinceStartup", inplace=True)
                    if not df_trial.empty:
                        if eye == "Right":
                            yaw_deg = df_trial["rEyeYaw"].to_numpy()
                        else:
                            yaw_deg = df_trial["lEyeYaw"].to_numpy()

                        start_time = df_trial["timeSinceStartup"].min()
                        end_time = df_trial["timeSinceStartup"].max()
                        df_trial["timeSinceStartup"] = df_trial["timeSinceStartup"] - start_time

                        m = np.isfinite(yaw_deg) 
                        t = df_trial["timeSinceStartup"].to_numpy()[m]
                        if merge_left_right and lat=='Left':
                            yaw_deg *= -1
                        v = yaw_deg[m]
                        # Unwrap angles to prevent interpolation issues at ±180°
                        v = np.unwrap(np.radians(v), discont=np.radians(180))
                        v = np.degrees(v)
                        

                        if v.size > 0:
                            ax.plot(v, t, lw=0.5, alpha=alpha, color=color)

                        # Store for average
                        yaw_trials.append((v, t))

                temporally_aligned_trials = []
                # Average across trials
                if yaw_trials:
                    # Find common time points (union of all time points)
                    all_times = np.arange(t_lim[0], t_lim[1], dt)  # 10 ms steps
                    # Interpolate each trial onto the common time points
                    for v, t in yaw_trials:   # v = yaw values, t = timestamps
                        interp_yaw = np.interp(all_times, t, v, left=np.nan, right=np.nan)  # use NaN for out-of-bounds
                        temporally_aligned_trials.append(interp_yaw)

                # Sum trial per time point for each quartile 
                active_trials_per_time_per_plot = np.isfinite(np.array(temporally_aligned_trials)).sum(axis=0) # ask if not a nan and then sums them, over time points to get sum of active trials at each time point

            if not(merge_left_right):
                
                ax.text(0.95*v_lim[0],0.95*t_lim[1],f"number of trials: {nb_data}",)
                
                # Sum trial per time point for each plot
                active_trials_per_time_per_plot = active_trials_per_time_per_plot.reshape(1,-1)
                
                X=active_trials_per_time_per_plot 
                X=X.T # vertical gradient
                X=np.flip(X) # vertical order flipped: bottom->top
                X=X/np.max(X) # normalize 0->100%
                ax.imshow(X*255, aspect='auto', cmap='Greys', extent=[v_lim[0],v_lim[1],t_lim[0],t_lim[1]])

                # Add horizontal line [50,75,95]% thresholds of gradient
                thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
                thresh_25 = all_times[-np.argmax(X>=0.25)]
                thresh_05 = all_times[-np.argmax(X>=0.05)]
        

                ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='50% trials active')
                ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
                ax.axhline(y=thresh_25, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='25% trials active')
                ax.text(v_lim[0]+5, thresh_25+0.05, '25% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
                ax.axhline(y=thresh_05, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='5% trials active')
                ax.text(v_lim[0]+5, thresh_05+0.05, '5% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
                 # Add vertical lines for pilars
                for angle in pilars_angle:
                    ax.axvline(x=angle, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                    ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
                elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                    ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[0]:
                    ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[1]:
                    ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            
        if merge_left_right:    
            
            ax.text(0.95*v_lim[0],0.95*t_lim[1],f"number of trials: {nb_data}",)

            # Sum trial per time point for each plot
            active_trials_per_time_per_plot = active_trials_per_time_per_plot.reshape(1,-1)

            X=active_trials_per_time_per_plot 
            X=X.T # vertical gradient
            X=np.flip(X) # vertical order flipped: bottom->top
            X=X/np.max(X) # normalize 0->100%
            ax.imshow(X*255, aspect='auto', cmap='Greys', extent=[v_lim[0],v_lim[1],t_lim[0],t_lim[1]])

            # Add horizontal line [50,75,95]% thresholds of gradient
            thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
            thresh_25 = all_times[-np.argmax(X>=0.25)]
            thresh_05 = all_times[-np.argmax(X>=0.05)]
    

            ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='50% trials active')
            ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
            ax.axhline(y=thresh_25, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='25% trials active')
            ax.text(v_lim[0]+5, thresh_25+0.05, '25% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
            ax.axhline(y=thresh_05, color='dimgrey', linestyle='-', linewidth=1, alpha=1, label='5% trials active')
            ax.text(v_lim[0]+5, thresh_05+0.05, '5% left', color='dimgrey', fontsize=8, va='bottom', ha='left')
            # Add vertical lines for pilars
            for angle in pilars_angle:
                ax.axvline(x=angle, color='gray', linestyle='--', linewidth=1, alpha=0.7)
            if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[1] and pos == position[0]:
                ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)
            elif lat == lateralisation[1] and pos == position[1]:
                ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1.5, alpha=0.9)

                    
                
        ax.set_xlim([v_lim[0], v_lim[1]])
        ax.set_xticks([-180, -90, 0, 90, 180])
        ax.set_yticks([0,1,2,3])
        ax.set_ylim([t_lim[0], t_lim[1]])


    fig.supxlabel('Yaw (degrees)')
    fig.supylabel('Time since trial start (s)')

    # --- build a generic 0→1 grayscale mappable (not tied to data) ---
    cmap = plt.get_cmap("Greys_r")           # or "Greys_r" to invert
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    # --- lock the layout of the subplots and reserve right margin ---
    # (Do NOT call a plain fig.tight_layout() after this.)
    fig.tight_layout(rect=[0, 0, 0.9, 0.9])   # keep 10% free on the right

    # --- add a dedicated colorbar axes (absolute figure coords) ---
    cbar_ax = fig.add_axes([0.92, 0.2, 0.02, 0.5])  # [left, bottom, width, height] in figure coords

    cb = fig.colorbar(sm, cax=cbar_ax, orientation='vertical')
    cb.set_label("Proportion of trials still active (%)")
    cb.set_ticks([0.0,0.25,0.5,0.75,1.0])
    cb.set_ticklabels(["100%","75%","50%","25%","0%"])


    fig.suptitle(
        f"Horizontal Eye Rotation",
        fontsize=16, y=1.05, x=0.5, horizontalalignment='center'
    )
    fig.text(
        s=f"All distractors conditions merged, Invalid/Valid Trials ",
        fontsize=12, y=1, x=0.5, horizontalalignment='center'
    )

    fig.legend(handles=legend_handles, title="Legend", loc="upper center", ncol=len(legend_handles), bbox_to_anchor=(0.5, 0.98))


    # ---------------- Save/Show ----------------
    if savepath:
        fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
    if show:
        plt.show()

    return fig, axes

def plot_temporal_y_rotation_by_distractor(
    df_track,
    *,
    eye: str = "Left",                       # "Left" or "Right"
    condition=("Valid",),                    # tuple/list of conditions to include (default: only "Valid")
    lateralisation=("Left", "Right"),
    position=("Front", "Rear"),
    nb_dist=("Zero", "One_near", "One_far", "Three"),
    band_percentiles = [[5,95],[25,75]],
    pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],               # angle of the pilars in degrees (0 = facing participant)   
    figsize=(10, 10),
    colors=["g"],
    median_colors=["darkgreen"],
    v_lim: tuple = (-180, 180),
    t_lim: tuple = (0, 3),
    dt = 0.01,                            # time step for interpolation (s)
    merge_left_right = True,
    savepath: str | None = None,             # e.g., "eye_displacement_plot_Valid.jpg"
    show: bool = True
):
    """
    Create a 4 subplot of rotation Y (y axis) over time across lateralisation and position

    Returns
    -------
    fig, axes
        fig, axes from matplotlib
    """
    plt.style.use('default')
 

    legend_handles = []

    # One handle per nb_dist for the median line (dashed, thicker)
    legend_handles += [
        Line2D([0], [0], color='g', lw=2, ls='--', label=f"median")
    ]

    # function to get alpha from percentile, goes from 0 to 1 at different rate
    get_alpha = lambda x: ((x/50)**0.3)/2
    # One handle per percentile for the shaded band
    for band_percentile in band_percentiles:
        legend_handles += [
            Patch(facecolor='g', alpha=get_alpha(band_percentile[0]), label=f"{band_percentile[0]}% & {band_percentile[1]}% percentile")
        ]


    # Pilars
    legend_handles.append(
        Line2D([0], [0], color='k', lw=1, linestyle='--', label='Pilars')
    )
    legend_handles.append(
        Line2D([0], [0], color='k', lw=2, linestyle='--', label='Pilar of Interest')
    )

    # ---------------- Validate inputs ----------------
    eye = eye.capitalize()
    if eye not in ("Left", "Right"):
        raise ValueError("eye must be 'Left' or 'Right'")

    # Columns required
    required_cols = {
        "lateralisation", "position", "condition", "nb_dist",
        "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
    }
    missing = required_cols - set(df_track.columns)
    if missing:
        raise ValueError(f"Missing required columns in df_track: {missing}")

    # ---------------- Prepare figure/grid ----------------
    if merge_left_right:  
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 0,
            f"{lateralisation[0]} {position[1]}": 1,
            f"{lateralisation[1]} {position[1]}": 1,
        }
        n_rows, n_cols = 4, 2
    else:
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 1,
            f"{lateralisation[0]} {position[1]}": 2,
            f"{lateralisation[1]} {position[1]}": 3,
        }
        n_rows, n_cols = 4, 4

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
    
    # ---------------- Plot per combination ---------------
    for l, dist in enumerate(nb_dist):
        for k,pos in enumerate(position):
            temporally_aligned_trials = []; nb_data = 0
            for j,lat in enumerate(lateralisation):
                if not(merge_left_right): temporally_aligned_trials = []; nb_data = 0
                for i, condi in enumerate(condition):

                    ax = axes[l][col_map[f"{lat} {pos}"]]
                    ax.set_xlim([v_lim[0], v_lim[1]])
                    ax.set_xticks([-180, -90, 0, 90, 180])
                    ax.set_yticks([0,1,2,3])
                    ax.set_ylim([t_lim[0], t_lim[1]])

                    if (j==0 or j==1) and l==0:
                        if merge_left_right:    ax.set_title(f"{pos}")
                        else:                   ax.set_title(f"{lat} {pos}")
                    if j==0 and k==0:           ax.set_ylabel(f"{dist}")
                    color = colors[0]
                    median_color = median_colors[0]
                
                    

                    # Filter rows for this combination (any of the selected conditions)
                    df_comb = df_track[
                        (df_track["lateralisation"] == lat) &
                        (df_track["position"] == pos) &
                        (df_track["nb_dist"] == dist) &
                        (df_track["condition"] == condi) 
                    ]

                    trials = df_comb["trial"].unique()

                    nb_data += len(trials)

                    # Store trials angle per time point
                    yaw_trials = []
                    for trial in trials:
                        df_trial = df_comb[df_comb["trial"] == trial].copy()
                        df_trial.sort_values("timeSinceStartup", inplace=True)
                        if not df_trial.empty:
                            if eye == "Right":
                                yaw_deg = df_trial["rEyeYaw"].to_numpy()
                            else:
                                yaw_deg = df_trial["lEyeYaw"].to_numpy()

                            start_time = df_trial["timeSinceStartup"].min()
                            end_time = df_trial["timeSinceStartup"].max()
                            df_trial["timeSinceStartup"] = df_trial["timeSinceStartup"] - start_time

                            m = np.isfinite(yaw_deg) 
                            t = df_trial["timeSinceStartup"].to_numpy()[m] # t = times
                            if merge_left_right and lat == "Left": yaw_deg *= -1
                            v = yaw_deg[m] # v = values

                            # Unwrap angles to prevent interpolation issues at ±180°
                            v = np.unwrap(np.radians(v), discont=np.radians(180))
                            v = np.degrees(v)

                            # Store for average
                            yaw_trials.append((v, t))
            
        
                    # Create common time grid for all trials
                    if yaw_trials:
                        # Common grid for everyone
                        all_times = np.arange(t_lim[0], t_lim[1], dt)  # 10 ms steps
                        for v, t in yaw_trials:

                            # Remove NaNs from the *values* so they don’t anchor interpolation
                            mask = ~np.isnan(v)
                            t_clean = t[mask]
                            v_clean = v[mask]
                            
                            # Ensure times are increasing
                            order = np.argsort(t_clean)
                            t_clean = t_clean[order]
                            v_clean = v_clean[order]

                            # Interpolate on the common grid; make OOB → NaN (no clamping)
                            interp_yaw = np.interp(all_times, t_clean, v_clean,
                                                left=np.nan, right=np.nan)
                            temporally_aligned_trials.append(interp_yaw)

                if not(merge_left_right) and temporally_aligned_trials:
                    temporally_aligned_trials = np.vstack(temporally_aligned_trials)

                    ax.text(0.9*v_lim[0],0.9*t_lim[1],f"number of trials: {nb_data}",)

                    # plot background gradient representing number of trials still active
                    active_trials_per_time = np.isfinite(np.array(temporally_aligned_trials)).sum(axis=0) # ask if not a nan and then sums them, over time points to get sum of active trials at each time point
                    X=np.broadcast_to(active_trials_per_time,(1,len(active_trials_per_time))) # 2D ARRAY
                    X=X.T # vertical gradient
                    X=np.flip(X) # vertical order flipped: bottom->top
                    X=X/np.max(X) # normalize 0->1
                    # Add horizontal line [50,25,5]% thresholds of gradient
                    thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
                    ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=0.7, label='50% trials active')
                    ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=5, va='bottom', ha='left')
                    
                    
                    # Loop through band_percentiles and alphas together
                    for band_percentile in band_percentiles:
                        percentile = np.nanpercentile(
                            temporally_aligned_trials, band_percentile[0],axis=0
                        )
                        opposite_percentile = np.nanpercentile(
                            temporally_aligned_trials, band_percentile[1],axis=0
                        )


                        mask = all_times <= thresh_50 # mask to plot only until 50% of active trials 
                        
                        ax.fill_betweenx(
                            all_times[mask], percentile[mask], opposite_percentile[mask],
                            color=color, alpha=get_alpha(band_percentile[0]), lw=1,
                        )

                        median_yaw = np.nanmedian(temporally_aligned_trials, axis=0)

                        ax.plot(
                            median_yaw[mask], all_times[mask],
                            color=median_color, lw=1.5, ls='--',
                            label=f"{condi} {dist} median"
                        )
                        
                    # Add vertical lines for pilars
                    for angle in pilars_angle:
                        ax.axvline(x=angle, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
                    if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                        ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                        ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[1] and pos == position[0]:
                        ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[1] and pos == position[1]:
                        ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    
                    # Add patch where too few trials
                    ax.add_patch(
                        patches.Rectangle(
                            (v_lim[0], thresh_50),           # (x, y) bottom-left corner
                            v_lim[1]-v_lim[0],  # width (until the end)
                            t_lim[1] - thresh_50,                # height
                            facecolor='none',           # transparent fill
                            hatch='////',               # diagonal stripes
                            edgecolor='gray',
                            linewidth=0.0,
                            alpha=0.3,
                            zorder=-1,                  # send behind data
                        )
                    )
                        

            if merge_left_right and temporally_aligned_trials:
                temporally_aligned_trials = np.vstack(temporally_aligned_trials)

                ax.text(0.9*v_lim[0],0.9*t_lim[1],f"number of trials: {nb_data}")

                # plot background gradient representing number of trials still active
                active_trials_per_time = np.isfinite(np.array(temporally_aligned_trials)).sum(axis=0) # ask if not a nan and then sums them, over time points to get sum of active trials at each time point
                X=np.broadcast_to(active_trials_per_time,(1,len(active_trials_per_time))) # 2D ARRAY
                X=X.T # vertical gradient
                X=np.flip(X) # vertical order flipped: bottom->top
                X=X/np.max(X) # normalize 0->1
                # Add horizontal line [50,25,5]% thresholds of gradient
                thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
                ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=0.7, label='50% trials active')
                ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=5, va='bottom', ha='left')
                
                
                # Loop through band_percentiles and alphas together
                for band_percentile in band_percentiles:
                    percentile = np.nanpercentile(
                        temporally_aligned_trials, band_percentile[0],axis=0
                    )
                    opposite_percentile = np.nanpercentile(
                        temporally_aligned_trials, band_percentile[1],axis=0
                    )


                    mask = all_times <= thresh_50 # mask to plot only until 50% of active trials 
                    
                    ax.fill_betweenx(
                        all_times[mask], percentile[mask], opposite_percentile[mask],
                        color=color, alpha=get_alpha(band_percentile[0]), lw=1
                    )

                    median_yaw = np.nanmedian(temporally_aligned_trials, axis=0)

                    ax.plot(
                        median_yaw[mask], all_times[mask],
                        color=median_color, lw=1.5, ls='--',
                        label=f"{condi} {dist} median"
                    )
                    
                # Add vertical lines for pilars
                for angle in pilars_angle:
                    ax.axvline(x=angle, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
                if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                    ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                    ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[0]:
                    ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[1]:
                    ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1, alpha=0.9)

                # Add patch where too few trials
                ax.add_patch(
                    patches.Rectangle(
                        (v_lim[0], thresh_50),           # (x, y) bottom-left corner
                        v_lim[1]-v_lim[0],  # width (until the end)
                        t_lim[1] - thresh_50,                # height
                        facecolor='none',           # transparent fill
                        hatch='////',               # diagonal stripes
                        edgecolor='gray',
                        linewidth=0.0,
                        alpha=0.3,
                        zorder=-1,                  # send behind data
                    )
                )
                        
                                

    fig.supxlabel('Yaw (degrees)')
    fig.supylabel('Time (s)')


    fig.suptitle(
        f"Horizontal Eye Rotation",
        fontsize=16, y=1.05, x=0.5, horizontalalignment='center'
    )
    fig.text(
        s=f"({condition} Trials)",
        fontsize=12, y=1.01, x=0.5, horizontalalignment='center'
    )

    fig.legend(handles=legend_handles, title="Legend", loc="upper center", ncol=len(legend_handles), bbox_to_anchor=(0.5,1.01))
    fig.tight_layout()

    # ---------------- Save/Show ----------------
    if savepath:
        fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
    if show:
        plt.show()

    return fig, axes

def plot_temporal_y_rotation_by_distractor_median(
    df_track,
    *,
    eye: str = "Left",                       # "Left" or "Right"
    condition=("Valid",),                    # tuple/list of conditions to include (default: only "Valid")
    lateralisation=("Left", "Right"),
    position=("Front", "Rear"),
    nb_dist=("Zero", "One_near", "One_far", "Three"),
    pilars_angle= [0,42,88,136,180,-180,-131,-90, -46],               # angle of the pilars in degrees (0 = facing participant)   
    figsize=(10, 10),
    colors=["g","purple"],
    v_lim: tuple = (-180, 180),
    t_lim: tuple = (0, 3),
    dt = 0.01,                            # time step for interpolation (s)
    slow_fast_threshold = 1.5,
    merge_left_right = True,
    savepath: str | None = None,             # e.g., "eye_displacement_plot_Valid.jpg"
    show: bool = True
):
    """
    Create a 4 subplot of rotation Y (y axis) over time across lateralisation and position

    Returns
    -------
    fig, axes
        fig, axes from matplotlib
    """
    plt.style.use('default')
 

    legend_handles = []

    # One handle per nb_dist for the median line (dashed, thicker)
    legend_handles += [
        Line2D([0], [0], color=colors[0], lw=2, ls='--', label=f"fast median"),
        Line2D([0], [0], color=colors[1], lw=2, ls='--', label=f"slow median"),

    ]



    # Pilars
    legend_handles.append(
        Line2D([0], [0], color='k', lw=1, linestyle='--', label='Pilars')
    )
    legend_handles.append(
        Line2D([0], [0], color='k', lw=2, linestyle='--', label='Pilar of Interest')
    )

    # ---------------- Validate inputs ----------------
    eye = eye.capitalize()
    if eye not in ("Left", "Right"):
        raise ValueError("eye must be 'Left' or 'Right'")

    # Columns required
    required_cols = {
        "lateralisation", "position", "condition", "nb_dist",
        "lEyeYaw", "lEyePitch", "rEyeYaw", "rEyePitch"
    }
    missing = required_cols - set(df_track.columns)
    if missing:
        raise ValueError(f"Missing required columns in df_track: {missing}")

    # ---------------- Prepare figure/grid ----------------
    if merge_left_right:  
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 0,
            f"{lateralisation[0]} {position[1]}": 1,
            f"{lateralisation[1]} {position[1]}": 1,
        }
        n_rows, n_cols = 4, 2
    else:
        col_map = {
            f"{lateralisation[0]} {position[0]}": 0,
            f"{lateralisation[1]} {position[0]}": 1,
            f"{lateralisation[0]} {position[1]}": 2,
            f"{lateralisation[1]} {position[1]}": 3,
        }
        n_rows, n_cols = 4, 4

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize, sharex=True, sharey=True)
    
    # ---------------- Plot per combination ---------------
    for l, dist in enumerate(nb_dist):
        for k,pos in enumerate(position):
            temporally_aligned_trials = []; nb_data = 0
            for j,lat in enumerate(lateralisation):
                if not(merge_left_right): temporally_aligned_trials = []; nb_data = 0
                for i, condi in enumerate(condition):

                    ax = axes[l][col_map[f"{lat} {pos}"]]
                    ax.set_xlim([v_lim[0], v_lim[1]])
                    ax.set_xticks([-180, -90, 0, 90, 180])
                    ax.set_yticks([0,1,2,3])
                    ax.set_ylim([t_lim[0], t_lim[1]])

                    if (j==0 or j==1) and l==0:
                        if merge_left_right:    ax.set_title(f"{pos}")
                        else:                   ax.set_title(f"{lat} {pos}")
                    if j==0 and k==0:           ax.set_ylabel(f"{dist}")
                
                    

                    # Filter rows for this combination (any of the selected conditions)
                    df_comb = df_track[
                        (df_track["lateralisation"] == lat) &
                        (df_track["position"] == pos) &
                        (df_track["nb_dist"] == dist) &
                        (df_track["condition"] == condi) 
                    ]

                    trials = df_comb["trial"].unique()

                    nb_data += len(trials)

                    # Store trials angle per time point
                    yaw_trials = []
                    for trial in trials:
                        df_trial = df_comb[df_comb["trial"] == trial].copy()
                        df_trial.sort_values("timeSinceStartup", inplace=True)
                        if not df_trial.empty:
                            if eye == "Right":
                                yaw_deg = df_trial["rEyeYaw"].to_numpy()
                            else:
                                yaw_deg = df_trial["lEyeYaw"].to_numpy()

                            start_time = df_trial["timeSinceStartup"].min()
                            end_time = df_trial["timeSinceStartup"].max()
                            df_trial["timeSinceStartup"] = df_trial["timeSinceStartup"] - start_time

                            m = np.isfinite(yaw_deg) 
                            t = df_trial["timeSinceStartup"].to_numpy()[m] # t = times
                            if merge_left_right and lat == "Left": yaw_deg *= -1
                            v = yaw_deg[m] # v = values

                            # Unwrap angles to prevent interpolation issues at ±180°
                            v = np.unwrap(np.radians(v), discont=np.radians(180))
                            v = np.degrees(v)

                            # Store for average
                            yaw_trials.append((v, t))
            
        
                    # Create common time grid for all trials
                    if yaw_trials:
                        # Common grid for everyone
                        all_times = np.arange(t_lim[0], t_lim[1], dt)  # 10 ms steps
                        for v, t in yaw_trials:

                            # Remove NaNs from the *values* so they don’t anchor interpolation
                            mask = ~np.isnan(v)
                            t_clean = t[mask]
                            v_clean = v[mask]
                            
                            # Ensure times are increasing
                            order = np.argsort(t_clean)
                            t_clean = t_clean[order]
                            v_clean = v_clean[order]

                            # Interpolate on the common grid; make OOB → NaN (no clamping)
                            interp_yaw = np.interp(all_times, t_clean, v_clean,
                                                left=np.nan, right=np.nan)
                            temporally_aligned_trials.append(interp_yaw)

                if not(merge_left_right) and temporally_aligned_trials:
                    temporally_aligned_trials = np.vstack(temporally_aligned_trials)

                    # plot background gradient representing number of trials still active
                    active_trials_per_time = np.isfinite(np.array(temporally_aligned_trials)).sum(axis=0) # ask if not a nan and then sums them, over time points to get sum of active trials at each time point
                    X=np.broadcast_to(active_trials_per_time,(1,len(active_trials_per_time))) # 2D ARRAY
                    X=X.T # vertical gradient
                    X=np.flip(X) # vertical order flipped: bottom->top
                    X=X/np.max(X) # normalize 0->1
                    # Add horizontal line [50,25,5]% thresholds of gradient
                    thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
                    ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=0.7, label='50% trials active')
                    ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=5, va='bottom', ha='left')
                    
                    ### Mask slow and fast trial
                    # Boolean mask of NaNs
                    isnan = np.isnan(temporally_aligned_trials)
                    # Get the first NaN index per row
                    first_nan_idx = np.where(isnan.any(axis=1),
                                            isnan.argmax(axis=1),  # first True along axis=1
                                            temporally_aligned_trials.shape[1])         # if no NaN, return last column index
                    finish_times = np.array([
                        all_times[i] if i < len(all_times) else np.nan
                        for i in first_nan_idx
                    ])
                    mask_fast = finish_times < slow_fast_threshold
                    median_yaw_fast = np.nanmedian(temporally_aligned_trials[mask_fast], axis=0)
                    median_yaw_slow = np.nanmedian(temporally_aligned_trials[~mask_fast], axis=0)
                    
                    ax.text(0.9*v_lim[0],0.9*t_lim[1],f"nb of fast trials: {mask_fast.sum()}", color=colors[0])
                    ax.text(0.9*v_lim[0],0.8*t_lim[1],f"nb of slow trials: {(~mask_fast).sum()}", color=colors[1])

                    ### Mask to plot only until 50% of active trials
                    mask_enough_data = all_times <= thresh_50 
                    ax.plot(
                        median_yaw_fast[mask_enough_data], all_times[mask_enough_data],
                        color=colors[0], lw=1.5, ls='--'
                    )
                    ax.plot(
                        median_yaw_slow[mask_enough_data], all_times[mask_enough_data],
                        color=colors[1], lw=1.5, ls='--',
                    )

                        
                    # Add vertical lines for pilars
                    for angle in pilars_angle:
                        ax.axvline(x=angle, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
                    if lat == lateralisation[0] and pos == position[0] and not(merge_left_right):
                        ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[0] and pos == position[1] and not(merge_left_right):
                        ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[1] and pos == position[0]:
                        ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    elif lat == lateralisation[1] and pos == position[1]:
                        ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                    
                    # Add patch where too few trials
                    ax.add_patch(
                        patches.Rectangle(
                            (v_lim[0], thresh_50),           # (x, y) bottom-left corner
                            v_lim[1]-v_lim[0],  # width (until the end)
                            t_lim[1] - thresh_50,                # height
                            facecolor='none',           # transparent fill
                            hatch='////',               # diagonal stripes
                            edgecolor='gray',
                            linewidth=0.0,
                            alpha=0.3,
                            zorder=-1,                  # send behind data
                        )
                    )
                        

            if merge_left_right and temporally_aligned_trials:
                temporally_aligned_trials = np.vstack(temporally_aligned_trials)

                ax.text(0.9*v_lim[0],0.9*t_lim[1],f"number of trials: {nb_data}")

                # plot background gradient representing number of trials still active
                active_trials_per_time = np.isfinite(np.array(temporally_aligned_trials)).sum(axis=0) # ask if not a nan and then sums them, over time points to get sum of active trials at each time point
                X=np.broadcast_to(active_trials_per_time,(1,len(active_trials_per_time))) # 2D ARRAY
                X=X.T # vertical gradient
                X=np.flip(X) # vertical order flipped: bottom->top
                X=X/np.max(X) # normalize 0->1
                # Add horizontal line [50,25,5]% thresholds of gradient
                thresh_50 = all_times[-np.argmax(X>=0.50)] # - because flipped
                ax.axhline(y=thresh_50, color='dimgrey', linestyle='-', linewidth=1, alpha=0.7, label='50% trials active')
                ax.text(v_lim[0]+5, thresh_50+0.05, '50% left', color='dimgrey', fontsize=5, va='bottom', ha='left')
                
                ### Mask slow and fast trial
                # Boolean mask of NaNs
                isnan = np.isnan(temporally_aligned_trials)
                # Get the first NaN index per row
                first_nan_idx = np.where(isnan.any(axis=1),
                                        isnan.argmax(axis=1),  # first True along axis=1
                                        temporally_aligned_trials.shape[1])         # if no NaN, return last column index
                finish_times = np.array([
                    all_times[i] if i < len(all_times) else np.nan
                    for i in first_nan_idx
                ])
                mask_fast = finish_times < slow_fast_threshold 

                ### Mask enough data to interpret median
                mask_enough_data = all_times <= thresh_50 # mask to plot only until 50% of active trials 

                median_yaw_fast = np.nanmedian(temporally_aligned_trials[mask_fast], axis=0)
                median_yaw_slow = np.nanmedian(temporally_aligned_trials[~mask_fast], axis=0)
                

                ax.plot(
                    median_yaw_fast[mask_enough_data], all_times[mask_enough_data],
                    color=colors[0], lw=1.5, ls='--',
                    label=f"{condi} {dist} median"
                )

                ax.plot(
                    median_yaw_slow[mask_enough_data], all_times[mask_enough_data],
                    color=colors[1], lw=1.5, ls='--',
                    label=f"{condi} {dist} median"
                )

                    
                # Add vertical lines for pilars
                for angle in pilars_angle:
                    ax.axvline(x=angle, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
                if lat == lateralisation[0] and pos == position[0]:
                    ax.axvline(x=pilars_angle[8], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[0] and pos == position[1]:
                    ax.axvline(x=pilars_angle[6], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[0]:
                    ax.axvline(x=pilars_angle[1], color='gray', linestyle='--', linewidth=1, alpha=0.9)
                elif lat == lateralisation[1] and pos == position[1]:
                    ax.axvline(x=pilars_angle[3], color='gray', linestyle='--', linewidth=1, alpha=0.9)

                # Add patch where too few trials
                ax.add_patch(
                    patches.Rectangle(
                        (v_lim[0], thresh_50),           # (x, y) bottom-left corner
                        v_lim[1]-v_lim[0],  # width (until the end)
                        t_lim[1] - thresh_50,                # height
                        facecolor='none',           # transparent fill
                        hatch='////',               # diagonal stripes
                        edgecolor='gray',
                        linewidth=0.0,
                        alpha=0.3,
                        zorder=-1,                  # send behind data
                    )
                )
                        
                                

    fig.supxlabel('Yaw (degrees)')
    fig.supylabel('Time (s)')


    fig.suptitle(
        f"Horizontal Eye Rotation",
        fontsize=16, y=1.05, x=0.5, horizontalalignment='center'
    )
    fig.text(
        s=f"{condi} Trials | Threshold slow/fast: {slow_fast_threshold} sec",
        fontsize=12, y=1.01, x=0.5, horizontalalignment='center'
    )

    fig.legend(handles=legend_handles, title="Legend", loc="upper center", ncol=len(legend_handles), bbox_to_anchor=(0.5,1.01))
    fig.tight_layout()

    # ---------------- Save/Show ----------------
    if savepath:
        fig.savefig(savepath, format=savepath.split(".")[-1], dpi=300, bbox_inches="tight")
    if show:
        plt.show()

    return fig, axes


def plot_eye_displacement_per_trial(df, trial_idx):

    # Extract trial
    df_trial = df[df["trial"] == int(trial_idx)]
    order = np.argsort(df_trial["timeSinceStartup"])

    x = df_trial["rEyeYaw"].to_numpy()[order]
    y = df_trial["rEyePitch"].to_numpy()[order]
    dt = np.diff(df_trial['timeSinceStartup'])
    dx = np.diff(x)
    dy = np.diff(y)

    dvx = dx/dt
    dvy = dy/dt

    dv = np.sqrt(dvx**2+dvy**2)

    # Create figure
    fig, ax = plt.subplots()

    # --- Load and overlay the image ---
    scene_img = mpimg.imread("fig/scene/360_view.jpg")

    # scene limits
    yaw_lim = [-180,180]
    pitch_lim = [-90,90]


    # Draw the image in the background
    ax.imshow(
        scene_img,
        extent=[yaw_lim[0], yaw_lim[1], pitch_lim[0], pitch_lim[1]],   # stretch image to data coords
        alpha=0.3,                         # transparency
        aspect='auto'
    )

    # ------------------ Build line segments ------------------
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # ------------------ Plot velocity-coded trajectory ------------------
    norm = LogNorm(vmin=10.0, vmax=1000.0)
    lc = LineCollection(segments, cmap="winter", linewidth=2, norm=norm)
    lc.set_array(dv)
    ax.add_collection(lc)
    cbar = plt.colorbar(lc, ax=ax)
    cbar.set_label("Velocity (deg/s)")

    ax.set_xlabel("Yaw")
    ax.set_ylabel("Pitch")
    ax.set_title(f"Trial {trial_idx}")

    plt.show()

def plot_reaction_vs_gazeOnset_time(df_trials, savefig = None):


    fig, ax = plt.subplots(1, figsize=(8, 6), sharex=True, sharey=True)
    fig.suptitle('Gaze-Onset Time vs. Reaction Time')

    unique_dist = ['Zero', 'One_near', 'One_far', 'Three']
    markers = ["$0$","$n$","$f$", "$3$"]

    colors = [['r', 'indianred', 'darkorange', 'gold'],['b', 'cyan', 'springgreen', 'g']]

    for position_i, position in enumerate(df_trials.position.unique()):
        df_pos = df_trials[
            (df_trials['position'] == position) &
            (df_trials['object_time'].notna()) &
            (df_trials['reaction_time'].notna()) & 
            (df_trials['object_time'] != 0)
                        ]
        color = colors[position_i]

        # ---- SCATTER -----
        for c, m, d in zip(color,markers, unique_dist):
            df_g = df_pos[df_pos['nb_dist'] == d]
            y = df_g['reaction_time'].to_numpy()
            x = df_g['object_time'].to_numpy()
            ax.scatter(x, y, s=20,color=c, marker=m, alpha= 0.6, label=f'{d}')

        # ----- REGRESSION -----    
        y = df_pos['reaction_time'].to_numpy()
        x = df_pos['object_time'].to_numpy()
        
        # correlation + regression
        r, p = stats.pearsonr(x, y)
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(0, 3, 100)
        y_line = m * x_line + b

        ax.plot(x_line, y_line, color=colors[position_i][0], linewidth=2, alpha=0.5, label="_nolegend_")
        
        text = f"{position}: r={r:.2f}\ny={m:.2f}x+{b:.2f}"

        ax.text(
            0.02, 0.95 - 0.1* position_i,   # vertical stacking per group
            text,
            transform=ax.transAxes,
            color=colors[position_i][0],
            fontsize=8,
            va="top"
            )
        
        
    ax.plot(x_line,x_line,color='k',ls='--',lw=1, label="_nolegend_")
    ax.set_ylabel("Total Reaction Time [s]")
    ax.set_xlabel("Time to Orient Gaze [s]")
    fig.legend(ncol=2, title='Distractors')

    plt.tight_layout()
    plt.show()
    if savefig:
        plt.savefig(savefig) 