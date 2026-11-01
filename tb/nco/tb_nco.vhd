library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity tb_nco is
end entity tb_nco;

architecture behavior of tb_nco is

    constant CLK_PERIOD : time := 10 ns;

    signal CLK_100MHZ : std_logic := '0';
    signal load        : std_logic := '0';
    signal dp20, dp21, dp22, dp23, dp24, dp25, dp26, dp27
        : std_logic_vector(31 downto 0) := (others => '0');
    signal val20, val21, val22, val23, val24, val25, val26, val27
        : std_logic_vector(15 downto 0);

begin

    CLK_100MHZ <= not CLK_100MHZ after CLK_PERIOD / 2;

    -- NCO instances
    NCO_20kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp20,
        value       => val20
    );

    NCO_21kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp21,
        value       => val21
    );
    
    NCO_22kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp22,
        value       => val22
    );

    NCO_23kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp23,
        value       => val23
    );

    NCO_24kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp24,
        value       => val24
    );

    NCO_25kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp25,
        value       => val25
    );

    NCO_26kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp26,
        value       => val26
    );

    NCO_27kHz : entity work.NCO
    port map(
        clk         => CLK_100MHZ,
        load        => load,
        delta_phase => dp27,
        value       => val27
    );

    stimulus : process
    begin
        -- Set coil frequencies
        dp20 <= std_logic_vector(to_unsigned(880468, 32));  -- 20.5 Hz
        dp21 <= std_logic_vector(to_unsigned(923418, 32));  -- 21.5 Hz
        dp22 <= std_logic_vector(to_unsigned(966368, 32));  -- 22.5 Hz
        dp23 <= std_logic_vector(to_unsigned(1009317, 32)); -- 23.5 Hz
        dp24 <= std_logic_vector(to_unsigned(1052267, 32)); -- 24.5 Hz
        dp25 <= std_logic_vector(to_unsigned(1095217, 32)); -- 25.5 Hz
        dp26 <= std_logic_vector(to_unsigned(1138166, 32)); -- 26.5 Hz
        dp27 <= std_logic_vector(to_unsigned(1181116, 32)); -- 27.5 Hz

        

        -- Load the frequency control value
        load <= '1';

        -- Wait for the rising edge
        wait until rising_edge(CLK_100MHZ);
        wait for 1 ns;

        -- Disable load
        load <= '0';

        wait;
    end process;

end behavior;