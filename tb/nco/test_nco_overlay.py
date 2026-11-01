
import csv
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer

CLK_FREQ = 100_000_000
PHASE_BITS = 32

FREQUENCIES = [
    20_000, 22_000, 24_000, 26_000,
    28_000, 30_000, 32_000, 34_000
]


@cocotb.test()
async def test_nco_overlay(dut):
    dut.clk.value = 0
    dut.load.value = 0
    dut.delta_phase.value = 0

    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    with open("nco_samples.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["frequency_hz", "time_us", "amplitude"])

        for freq in FREQUENCIES:
            # Calculate phase increment
            step = round(freq * 2**PHASE_BITS / CLK_FREQ)

            # Load new frequency
            dut.delta_phase.value = step
            dut.load.value = 1
            await Timer(20, unit="ns")
            dut.load.value = 0
            await Timer(10, unit="ns")

            # Record 200 us of output
            for n in range(400):
                await Timer(500, unit="ns")

                raw = int(dut.value.value)

                # Convert 16-bit value to signed integer
                amplitude = raw if raw < 32768 else raw - 65536

                writer.writerow([freq, (n + 1) * 0.5, amplitude])

            dut._log.info(f"Recorded {freq / 1000:g} kHz")

    dut._log.info("All frequencies recorded")
