
import csv
import matplotlib.pyplot as plt

data = {}

with open("nco_samples.csv", "r") as file:
    reader = csv.DictReader(file)

    for row in reader:
        freq = int(row["frequency_hz"])
        time = float(row["time_us"])
        amplitude = int(row["amplitude"])

        if freq not in data:
            data[freq] = {"time": [], "amplitude": []}

        data[freq]["time"].append(time)
        data[freq]["amplitude"].append(amplitude)

plt.figure(figsize=(12, 6))

for freq, samples in data.items():
    plt.plot(
        samples["time"],
        samples["amplitude"],
        label=f"{freq / 1000:g} kHz",
        linewidth=1
    )

plt.title("NCO Frequency Comparison")
plt.xlabel("Time (µs)")
plt.ylabel("Signed Amplitude")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig("nco_overlay.png", dpi=200)
plt.show()
