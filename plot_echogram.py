import argparse
from pathlib import Path
import numpy as np
import echopype as ep
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
from scipy.ndimage import median_filter, gaussian_filter

def mask_top_and_bottom_bands(s, near_field_m=2.0, surface_buffer_m=2.0):
    """
    Blanks out the transducer near-field ringdown (bottom band) and the
    dynamic sea surface reflection (top band) for an upward-looking sonar.
    """
    # 1. Mask the Bottom Band (Initial Transmit Pulse Near-Field)
    s = s.where(s.range_m > near_field_m)

    # 2. Mask the Top Band (Dynamic Sea Surface Line)
    search_zone = s.where(s.range_m > 4.0)
    surface_idx = search_zone.argmax(dim="range_m")
    surface_range_m = s.range_m.isel(range_m=surface_idx)
    
    under_surface_mask = s.range_m < (surface_range_m - surface_buffer_m)
    s = s.where(under_surface_mask)
    
    return s

def smooth_vertical_and_horizontal_banding(s, median_kernel=(3, 11), gaussian_sigma=(1, 2)):
    """
    Applies 2D spatial image filters to suppress thin vertical noise spikes
    and smooth mid-section horizontal background striping fields.
    """
    sv_matrix = s.values.copy()
    
    mask_nan = np.isnan(sv_matrix)
    if np.any(mask_nan):
        sv_matrix[mask_nan] = -100.0

    # Stage 1: Horizontal median filter kills thin vertical transient lines
    smoothed = median_filter(sv_matrix, size=median_kernel)
    
    # Stage 2: Vertical Gaussian blur blends away horizontal background bands
    smoothed = gaussian_filter(smoothed, sigma=gaussian_sigma)
    
    smoothed[mask_nan] = np.nan
    return xr.DataArray(smoothed, coords=s.coords, dims=s.dims)

def process_file(file_path, output_dir, target_freq="120"):
    """Processes a single EBS survey .raw file tuned for high-frequency broadband ML training."""
    try:
        print(f"\nProcessing: {file_path.name}")
        ed = ep.open_raw(str(file_path), sonar_model="EK80")
        
        # --- Fallback Loop for Broadband / FM Datasets ---
        sv = None
        for mode, enc in [("BB", "complex"), ("FM", "complex")]:
            try:
                print(f"Attempting to compute Sv using waveform_mode='{mode}'...")
                sv = ep.calibrate.compute_Sv(ed, waveform_mode=mode, encode_mode=enc)
                print(f"Successfully calibrated using {mode} mode.")
                break
            except Exception as mode_err:
                print(f"Mode {mode} unavailable or failed: {mode_err}")
                continue
                
        if sv is None:
            print(f"Skipping {file_path.name}: No valid Broadband (BB) or FM data found.")
            return

        # --- Step 1. Apply Tuned Background Noise Removal Before Slicing/Filling ---
        print("Denoising horizontal bands via De Robertis algorithm...")
        try:
            # TUNED: Increased cell sizes (40 pings, 60 samples) to prevent over-subtraction blur
            sv = ep.clean.remove_background_noise(
                ds_Sv=sv,
                ping_num=40,               
                range_sample_num=60,       
                background_noise_max=-125, 
                SNR_threshold="3.0dB"      
            )
        except Exception as denoising_error:
            print(f"Warning: Clean module failed, proceeding with raw data. Info: {denoising_error}")

        # --- Select High-Frequency Channel (70, 120, or 200) ---
        ch = None
        for i, name in enumerate(sv.channel.values):
            if target_freq in str(name):
                ch = i
                break
        
        if ch is None:
            print(f"Skipping {file_path.name}: {target_freq} kHz broadband channel not found.")
            return

        print(f"Using channel {ch}: {sv.channel.values[ch]}")
        s = sv["Sv"].isel(channel=ch)

        # Assign true depth range metrics in meters
        r = sv["echo_range"].isel(channel=ch).median("ping_time").values
        r = r[: s.sizes["range_sample"]]
        s = s.assign_coords(range_sample=r).rename(range_sample="range_m")

        # --- Step 2. Remove Bottom Near-Field and Top Surface Boundary Noise ---
        print("Masking boundary bands...")
        s = mask_top_and_bottom_bands(s, near_field_m=2.5, surface_buffer_m=2.0)

        # --- TUNED: Shallow-to-Midwater Depth Window (10 to 25m) ---
        min_depth = 10
        max_depth = 25
        
        min_idx = int(np.searchsorted(s["range_m"].values, min_depth))
        max_idx = int(np.searchsorted(s["range_m"].values, max_depth))
        s = s.isel(range_m=slice(min_idx, max_idx))

        # Robust Background Masking (Replaces both NaNs and low SNR masked regions)
        s = s.fillna(-100.0)
        
        if s.sizes["ping_time"] == 0 or s.sizes["range_m"] == 0:
            print(f"Skipping {file_path.name}: Sliced matrix contains no data elements.")
            return

        # --- PLOTTING (ML OPTIMIZED WITH SHARP DATA FEATURES) ---
        fig, ax = plt.subplots(figsize=(6.4, 6.4))
        
        ax.imshow(
            s.T.values,
            extent=[0, s.sizes["ping_time"], float(s.range_m.min()), float(s.range_m.max())],
            vmin=-70, 
            vmax=-10, 
            cmap="gray",
            origin="lower",  
            aspect="auto",
            interpolation="nearest" # Keeps individual crisp pixel metrics sharp and distinct
        )

        # Hard crops image bounds to prevent outer canvas layout stretching
        ax.set_ylim(float(s.range_m.max()), float(s.range_m.min()))

        # Strip all human-facing metadata labels to preserve clean ML tensors
        ax.set_axis_off()
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

        # Save directly to the training set directory
        out_path = output_dir / f"{file_path.stem}_{target_freq}kHz-2.png"
        plt.savefig(out_path, dpi=100, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        print(f"Successfully saved sharp {target_freq}kHz frame: {out_path.name}")

    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process EBS Pollock survey raw files into clean high-frequency data.")
    parser.add_argument("input_path", help="Path to a single EK80 file or folder of EBS data")
    parser.add_argument("-f", "--frequency", default="120", choices=["70", "120", "200"], 
                        help="Target frequency channel to extract (default: 120)")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_dir = Path("training_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        raw_files = sorted(list(input_path.glob("*.raw")) + list(input_path.glob("*.RAW")))
        print(f"Found {len(raw_files)} survey files in directory.")
        for file_path in raw_files:
            process_file(file_path, output_dir, target_freq=args.frequency)
    elif input_path.is_file():
        process_file(input_path, output_dir, target_freq=args.frequency)
    else:
        print(f"Error: Path '{args.input_path}' not found.")
