library IEEE; 
use IEEE.std_logic_1164.all; 
use IEEE.numeric_std.all;
use work.sine_rom_pkg.all;

entity NCO is
    generic(
        LGTBL       : integer := 12;
        PHASE_BITS  : integer := 32
    );
    port(
        clk         : in std_logic;
        load        : in std_logic;
        delta_phase : in std_logic_vector(PHASE_BITS-1 downto 0);
        value       : out std_logic_vector(15 downto 0)
    );
end entity ;

architecture behavior of NCO is
    signal phase_acc    : unsigned(PHASE_BITS-1 downto 0):= (others => '0');
    signal phase_step   : unsigned(PHASE_BITS-1 downto 0):= (others => '0');
    signal lut_address  : unsigned(LGTBL-1 downto 0):= (others => '0');


begin
    lut_address <= phase_acc(PHASE_BITS-1 downto PHASE_BITS-LGTBL);
    value <= SINE_ROM(to_integer(lut_address));

    phase_accumulator : process(clk)
    begin 
        
        if rising_edge(clk) then
            
            if load = '1' then
                phase_step <= unsigned(delta_phase);
            end if;
            
            phase_acc <= phase_acc + phase_step;
        end if;
    end process;

end behavior;