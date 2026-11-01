
import math
from pathlib import Path
from fractions import Fraction

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# 1. PROJECT CONSTANTS
# ============================================================

F_XO = 32_768_000       # Crystal clock frequency (Hz)
DIV = 164               # Clock cycles per DAC update
M = 1                   # Speed factor (initially 1)

K_LIST = range(10, 18)  # Eight tones: k = 10 to 17

TABLE_SIZE = 4096       # 12-bit ROM address space
AMP = 32767             # Signed 16-bit amplitude
N_UPDATES = 4096        # Number of output updates

PHASE_BITS = 32
INDEX_BITS = 12
LOW_BITS = PHASE_BITS - INDEX_BITS

# Find the project root automatically
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEN_DIR = PROJECT_ROOT / "gen"
PLOT_DIR = GEN_DIR / "plots"
RTL_DIR = PROJECT_ROOT / "rtl" / "nco"


# ============================================================
# 2. GENERATE SINE LOOKUP TABLE
# ============================================================

def make_sine_table():
    """Generate 4096 signed 16-bit sine samples."""

    table = []

    for i in range(TABLE_SIZE):
        angle = (2 * math.pi * i) / TABLE_SIZE
        value = round(AMP * math.sin(angle))
        table.append(value)

    # Sanity checks
    assert len(table) == TABLE_SIZE
    assert table[0] == 0
    assert table[1024] == 32767
    assert table[2048] == 0
    assert table[3072] == -32767

    assert all(-AMP <= value <= AMP for value in table)

    return table


# ============================================================
# 3. OPTIMIZED 12-BIT DDS INDEX
# ============================================================

def shortcut_index(k, n):
    """Calculate the sine ROM index using the shortcut."""

    index = (41 * k * M * n) % TABLE_SIZE
    return index


# ============================================================
# 4. ORIGINAL 32-BIT DDS REFERENCE
# ============================================================

def accumulator_index(k, n):
    """Calculate the original DDS index and its low 20 bits."""

    # Frequency tuning word
    ftw = k * 262144

    # Original 32-bit phase
    phase = (n * DIV * M * ftw) % (2 ** PHASE_BITS)

    # Upper 12 bits select the sine ROM address
    index = phase >> LOW_BITS

    # Lower 20 bits
    low_bits = phase % (2 ** LOW_BITS)

    return index, low_bits


# ============================================================
# 5. CONVERT SIGNED SAMPLE TO DAC WORD
# ============================================================

def to_dac_word(s):
    """Convert signed sine amplitude to offset binary."""

    assert -AMP <= s <= AMP

    dac_word = s + 32768

    assert 1 <= dac_word <= 65535

    return dac_word


# ============================================================
# 6. GENERATE VHDL SINE ROM PACKAGE
# ============================================================

def write_vhdl_package(table, path):
    """Write the sine lookup table as a VHDL package."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:

        f.write("library ieee;\n")
        f.write("use ieee.std_logic_1164.all;\n\n")

        f.write("package sine_rom_pkg is\n\n")

        f.write(
            "    type sine_rom_t is array (0 to 4095) "
            "of std_logic_vector(15 downto 0);\n\n"
        )

        f.write("    constant SINE_ROM : sine_rom_t := (\n")

        for i, value in enumerate(table):

            # Convert signed value to 16-bit two's complement
            hex_value = value & 0xFFFF

            # No comma after the final entry
            comma = "," if i < len(table) - 1 else ""

            # Four entries per line
            if i % 4 == 0:
                f.write("        ")

            f.write(f'{i} => x"{hex_value:04X}"{comma}')

            if i % 4 == 3 or i == len(table) - 1:
                f.write("\n")
            else:
                f.write("  ")

        f.write("    );\n\n")
        f.write("end package sine_rom_pkg;\n")

    print("PASS: VHDL sine ROM package generated")


# ============================================================
# 7. GENERATE EXPECTED DAC OUTPUT FILE
# ============================================================

def write_expected(table, path):
    """Generate expected DAC words for all eight channels."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:

        for n in range(N_UPDATES):

            words = []

            for k in K_LIST:

                # Phase BEFORE the nth step
                index = shortcut_index(k, n)

                # Read signed amplitude from sine ROM
                sample = table[index]

                # Convert amplitude to offset binary
                dac_word = to_dac_word(sample)

                # Format as four-digit hexadecimal
                words.append(f"{dac_word:04X}")

            # One line per update, eight DAC words
            f.write(" ".join(words) + "\n")

    print("PASS: Expected DAC output file generated")


# ============================================================
# 8. VERIFY DDS EQUIVALENCE
# ============================================================

def check_equivalence():
    """Verify shortcut equals the original DDS exactly."""

    for k in K_LIST:
        for n in range(N_UPDATES):

            shortcut = shortcut_index(k, n)
            reference, low_bits = accumulator_index(k, n)

            assert shortcut == reference, (
                f"Index mismatch: k={k}, n={n}"
            )

            assert low_bits == 0, (
                f"Nonzero low bits: k={k}, n={n}"
            )

    print("PASS: 12-bit shortcut matches 32-bit DDS")
    print(f"       Checked {len(K_LIST) * N_UPDATES} cases")


# ============================================================
# 9. VERIFY EXACT OUTPUT FREQUENCIES
# ============================================================

def check_frequencies():
    """Verify DDS frequencies using exact rational arithmetic."""

    print("\nExact output frequencies:")

    # The given 2*k kHz targets apply at M=1.
    assert M == 1, "This frequency check expects M=1"

    sample_rate = Fraction(F_XO, DIV * M)

    for k in K_LIST:

        frequency = (
            Fraction(41 * k, TABLE_SIZE) * sample_rate
        )

        expected_frequency = 2000 * k

        assert frequency == expected_frequency, (
            f"Frequency mismatch for k={k}"
        )

        print(f"  k={k}: {frequency} Hz")

    print("PASS: All eight frequencies are exact")


# ============================================================
# 10. GENERATE CHANNEL DATA
# ============================================================

def generate_channel_data(table):
    """Generate the DAC data as a NumPy array."""

    data = []

    for n in range(N_UPDATES):

        row = []

        for k in K_LIST:

            index = shortcut_index(k, n)
            sample = table[index]
            dac_word = to_dac_word(sample)

            row.append(dac_word)

        data.append(row)

    return np.array(data, dtype=np.int64)


# ============================================================
# 11. FFT VERIFICATION
# ============================================================

def check_fft(data):
    """Verify the eight tones occupy the expected FFT bins."""

    # Convert DAC words back to signed samples
    signed_data = data - 32768

    # Sum all eight channels
    combined = np.sum(signed_data, axis=1)

    # Compute 4096-point FFT without a window
    fft_values = np.fft.rfft(combined, n=N_UPDATES)

    magnitudes = np.abs(fft_values)

    # Expected bins for k=10 to 17
    expected_bins = {41 * k for k in K_LIST}

    # Find eight largest non-DC FFT bins
    ranked_bins = np.argsort(magnitudes[1:])[-8:] + 1

    found_bins = set(int(b) for b in ranked_bins)

    assert found_bins == expected_bins, (
        f"FFT mismatch: found {sorted(found_bins)}"
    )

    # Find strongest expected tone
    tone_peak = max(magnitudes[b] for b in expected_bins)

    # Find strongest component outside expected tones
    other_magnitudes = magnitudes.copy()

    for b in expected_bins:
        other_magnitudes[b] = 0

    other_magnitudes[0] = 0

    largest_other = np.max(other_magnitudes)

    if largest_other > 0:
        other_dbc = 20 * np.log10(largest_other / tone_peak)
    else:
        other_dbc = float("-inf")

    print("PASS: Eight largest FFT bins are correct")
    print("       FFT bins:", sorted(found_bins))
    print(f"       Largest other component: {other_dbc:.2f} dBc")

    return fft_values, magnitudes


# ============================================================
# 12. TIME DOMAIN PLOT
# ============================================================


def plot_time_domain(data, path):
    """Plot the eight DDS channels in separate subplots."""

    sample_rate = F_XO / (DIV * M)

    time = np.arange(N_UPDATES) / sample_rate

    # Convert DAC words to volts
    voltages = data / 65535 * 5.0

    # Display first 0.5 ms
    mask = time <= 0.0005

    fig, axes = plt.subplots(
        8, 1,
        figsize=(12, 12),
        sharex=True
    )

    for channel, k in enumerate(K_LIST):

        axes[channel].plot(
            time[mask] * 1000,
            voltages[mask, channel],
            marker=".",
            markersize=3,
            linewidth=1
        )

        axes[channel].set_ylabel(
            f"{2 * k} kHz\n(V)"
        )

        axes[channel].set_ylim(-0.2, 5.2)
        axes[channel].grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (ms)")

    fig.suptitle(
        "DDS Golden Model - Eight Output Channels",
        fontsize=14
    )

    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


# ============================================================
# 13. FREQUENCY SPECTRUM PLOT
# ============================================================

def plot_spectrum(magnitudes, path):
    """Plot the FFT spectrum in dB."""

    sample_rate = F_XO / (DIV * M)

    frequencies = np.fft.rfftfreq(
        N_UPDATES,
        d=1 / sample_rate
    )

    # Normalize relative to the largest spectral component
    peak = np.max(magnitudes)

    # Avoid log10(0)
    normalized = np.maximum(
        magnitudes / peak,
        1e-15
    )

    spectrum_db = 20 * np.log10(normalized)

    plt.figure(figsize=(12, 6))

    plt.plot(
        frequencies / 1000,
        spectrum_db,
        linewidth=1
    )

    plt.title("DDS Output - Frequency Spectrum")
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("Magnitude (dB relative to peak)")

    plt.xlim(0, 50)
    plt.ylim(-120, 5)

    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()

    print("PASS: Spectrum plot generated")


# ============================================================
# 14. MAIN PROGRAM
# ============================================================

def main():

    print("====================================")
    print("       DDS GOLDEN MODEL")
    print("====================================\n")

    # Create output directories
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate sine table
    sine_table = make_sine_table()

    print("PASS: Sine table generated")
    print("       Entries:", len(sine_table))
    print("       Minimum:", min(sine_table))
    print("       Maximum:", max(sine_table))

    # Step 2: Check shortcut steps
    for k in K_LIST:
        step = shortcut_index(k, 1)
        assert step == (41 * k * M) % TABLE_SIZE

    print("PASS: Shortcut index steps")

    # Step 3: Verify DDS equivalence
    check_equivalence()

    # Step 4: Verify DAC conversion
    assert to_dac_word(0) == 32768
    assert to_dac_word(32767) == 65535
    assert to_dac_word(-32767) == 1

    print("PASS: DAC conversion")

    # Step 5: Verify exact frequencies
    check_frequencies()

    # Step 6: Generate VHDL package
    write_vhdl_package(
        sine_table,
        RTL_DIR / "sine_rom_pkg.vhd"
    )

    # Step 7: Generate expected DAC file
    write_expected(
        sine_table,
        GEN_DIR / "expected_dac_words.txt"
    )

    # Step 8: Generate all channel samples
    data = generate_channel_data(sine_table)

    # Verify output dimensions
    assert data.shape == (N_UPDATES, len(K_LIST))

    # Line zero must be all midscale
    assert np.all(data[0] == 32768)

    # Step 9: Verify FFT
    fft_values, magnitudes = check_fft(data)

    # Step 10: Generate time-domain plot
    plot_time_domain(
        data,
        PLOT_DIR / "time_domain.png"
    )

    # Step 11: Generate frequency spectrum
    plot_spectrum(
        magnitudes,
        PLOT_DIR / "spectrum.png"
    )

    print("\n====================================")
    print("      ALL CHECKS COMPLETED")
    print("====================================")

    print("\nGenerated files:")
    print(RTL_DIR / "sine_rom_pkg.vhd")
    print(GEN_DIR / "expected_dac_words.txt")
    print(PLOT_DIR / "time_domain.png")
    print(PLOT_DIR / "spectrum.png")


if __name__ == "__main__":
    main()
