from pathlib import Path

import h5py
import numpy as np
from PIL import Image

directory = Path("NC_data")

for source in directory.glob("*.nc"):
    print(f"Processing {source}")
    output = Path("Echograms") / (source.stem + ".png")
    output.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(source, "r") as nc:
        envelope = np.asarray(nc["compressed_env"][:], dtype=np.float32)

    # Display relative envelope strength in dB; this is not calibrated Sv.
    db = 20 * np.log10(np.maximum(envelope, 1e-12))
    low, high = np.percentile(db[np.isfinite(db)], [1, 99.5])
    if high <= low:
        raise ValueError("The envelope has no usable display range.")

    pixels = np.clip((db.T - low) / (high - low), 0, 1)
    Image.fromarray((pixels * 255).astype(np.uint8)).save(output)
    print(f"Saved {output}")