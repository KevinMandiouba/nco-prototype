import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer


@cocotb.test()
async def test_nco_20khz(dut):

    # Initialize inputs
    dut.clk.value = 0
    dut.load.value = 0
    dut.delta_phase.value = 858993

    # Generate 100 MHz clock
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    # Load the phase increment
    dut.load.value = 1
    await Timer(20, unit="ns")
    dut.load.value = 0

    # Simulate four periods of a 20 kHz signal
    await Timer(200, unit="us")

    dut._log.info("20 kHz NCO simulation completed")