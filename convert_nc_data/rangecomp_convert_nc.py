from pathlib import Path

import h5py
import numpy as np
from PIL import Image

directory = Path("NC_data")

for source in directory.glob("*.nc"):
    print(f"Processing {source}")
    output = Path("RangeCompEchograms") / (source.stem + ".png")
    output.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(source, "r") as nc:
        envelope = np.asarray(nc["compressed_env"][:], dtype=np.float32)

    # Display envelope level with a range compensation.
    # Set this from the recording's frequency and water conditions; 0 disables absorption.
    ABSORPTION_DB_PER_M = 0.0
    REFERENCE_RANGE_M = 1.0

    with h5py.File(source, "r") as nc:
        envelope = np.asarray(nc["compressed_env"][:], dtype=np.float32)
        range_m = np.asarray(nc["range"][:], dtype=np.float32)

    # Assumes compressed_env is a linear-amplitude envelope.
    db = 20 * np.log10(np.maximum(envelope, 1e-12))

    # Ignore nonpositive ranges, which cannot be used in the correction.
    valid_range = range_m > 0
    r = range_m[valid_range]
    range_loss_db = (
        20 * np.log10(r / REFERENCE_RANGE_M)
        + 2 * ABSORPTION_DB_PER_M * (r - REFERENCE_RANGE_M)
    )
    db[:, valid_range] += range_loss_db[None, :]
    db[:, ~valid_range] = np.nan

    # Scale for display after compensation; compensation can increase distant noise.
    finite = db[np.isfinite(db)]
    low, high = np.percentile(finite, [1, 99.5])
    if high <= low:
        raise ValueError("The envelope has no usable display range.")

    pixels = np.clip((db.T - low) / (high - low), 0, 1)
    pixels = np.nan_to_num(pixels, nan=0.0)
    Image.fromarray((pixels * 255).astype(np.uint8)).save(output)
    print(f"Saved {output}")