import argparse
from pathlib import Path

import echopype as ep
import matplotlib.pyplot as plt

#pass the .raw file path in when running (python plot_echogram.py <file>)
parser = argparse.ArgumentParser(description="Plot an echogram from an EK80 .raw file.")
parser.add_argument("raw_file", help="path to the EK80 .raw file")
parser.add_argument("-o", "--output", help="where to save the plot (default: <raw file name>.png in the current folder)")
args = parser.parse_args()
f = args.raw_file
ed = ep.open_raw(f, sonar_model="EK80")
print(ed)

#compute Sv, try broadband first and fall back to narrowband if the file doesn't have it
sv = None
for mode, enc in [("BB", "complex"), ("CW", "complex"), ("CW", "power")]:
    try:
        sv = ep.calibrate.compute_Sv(ed, waveform_mode=mode, encode_mode=enc)
        print("Worked with", mode, enc)
        break
    except Exception as e:
        print("Failed with", mode, enc, "->", e)

#print how much data each channel has (used for picking ch)
for i, name in enumerate(sv.channel.values):
    n = int(sv["Sv"].isel(channel=i).notnull().sum())
    print(i, name, "values with data:", n)

ch = 3  

#drop empty pings/samples and swap sample index for range in meters
s = sv["Sv"].isel(channel=ch)
s = s.dropna("ping_time", how="all").dropna("range_sample", how="all")
r = sv["echo_range"].isel(channel=ch).median("ping_time").values
r = r[: s.sizes["range_sample"]]
s = s.assign_coords(range_sample=r).rename(range_sample="range_m")
print(s.sizes, "range from", float(s.range_m.min()), "to", float(s.range_m.max()), "m")

#zoom to 10-25 m and flip y so it reads looking up (upward facing transducer)
s = s.sel(range_m=slice(10, 25))
s.T.plot(vmin=-70, vmax=-30, cmap="RdBu_r", yincrease=True)
plt.ylabel("Range from transducer, looking up (m)")

#save before showing (closing the window clears the figure)
out = args.output or Path(f).stem + ".png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print("Saved plot to", out)
plt.show()