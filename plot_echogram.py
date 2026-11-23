from pathlib import Path
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

# Relative to current working directory 
input_folder = Path("raw_image_files")
output_folder = Path("images")
output_folder.mkdir(parents=True, exist_ok=True)

# False = process only the first 5 files for validation
# True  = process all matching files in input_folder
process_all = True

extensions = {".nc"}
nc_files = sorted(
    f
    for f in input_folder.iterdir()
    if f.is_file() and f.suffix.lower() in extensions
)

files_to_process = nc_files if process_all else nc_files[:5]
print(f"Processing {len(files_to_process)} of {len(nc_files)} files...")


def export_grayscale_echogram(nc_path: Path, out_path: Path) -> None:
  with nc.Dataset(nc_path, mode="r") as ds:
    time = np.asarray(ds.variables["time"][:]).squeeze()
    range_val = np.asarray(ds.variables["range"][:]).squeeze()
    compressed_env = np.asarray(ds.variables["compressed_env"][:]).squeeze()

  # Ensure shape is (len(range), len(time))
  if compressed_env.shape == (len(time), len(range_val)) and len(time) != len(
      range_val
  ):
    compressed_env = compressed_env.T

  # Convert envelope to dB (20*log10 for amplitude/envelope; use 10.0 if already power)
  env_db = 20.0 * np.log10(np.maximum(np.abs(compressed_env), 1e-30))

  # Slice to 5-20 m first so no blank area appears below range_val.min()
  r_min, r_max = 5.0, 20.0
  mask = (range_val >= r_min) & (range_val <= r_max)
  range_sub = range_val[mask]
  env_sub = env_db[mask, :]

  fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
  fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
  ax.margins(0)

  y_bottom = range_sub.min() if len(range_sub) > 0 else r_min
  y_top = range_sub.max() if len(range_sub) > 0 else r_max

  ax.imshow(
      env_sub,
      cmap="gray",
      origin="lower",  
      aspect="auto",
      interpolation="nearest",  # Sharp sample edges instead of bilinear blur
      extent=[time.min(), time.max(), y_bottom, y_top],
      vmin=-70,  
      vmax=-40,
  )

  ax.set_xlim(time.min(), time.max())
  ax.set_ylim(r_min, r_max)
  ax.axis("off")

  plt.savefig(
      out_path,
      dpi=300,
      bbox_inches="tight",
      pad_inches=0,
  )
  plt.close(fig)


for nc_path in files_to_process:
  out_path = output_folder / f"{nc_path.stem}.png"
  export_grayscale_echogram(nc_path, out_path)
  print(f"Saved: {out_path}")