"""
LED Blinker circuit using TLC555 timer in astable mode.
Power: 5V-9V battery, blinks one LED at ~1Hz.
Architecture: Battery → (optional Schottky protection) → TLC555 astable → LED with current-limiting resistor.

Generated from architecture JSON (solver_ready_v3), component selection JSON, and schematic instantiation JSON.
"""

import unittest

from typing_extensions import override

from edg import *


class Tlc555_Device(FootprintBlock):
    """TLC555 CMOS 555 Timer IC - FootprintBlock with pin-level definition.

    Pin assignment (DIP-8 / SOIC-8):
      1: GND
      2: TRIG (trigger input)
      3: OUT (output)
      4: RESET (active low, tie to VCC for normal operation)
      5: CTRL (control voltage, typically filtered with cap to GND)
      6: THR (threshold input)
      7: DISCH (discharge, open-drain output)
      8: VCC (power supply)
    """

    def __init__(self) -> None:
        super().__init__()
        self.vcc = self.Port(VoltageSink(
            voltage_limits=(2, 15) * Volt,
            current_draw=(0.01, 1) * mAmp  # TLC555 CMOS: typ 0.36mA quiescent
        ))
        self.gnd = self.Port(Ground())
        self.out = self.Port(DigitalSource.from_supply(
            self.gnd, self.vcc,
            current_limits=(-10, 10) * mAmp,
            output_threshold_offset=(0.1, -0.1)
        ))
        # Analog/timing pins exposed as Passive
        self.trig = self.Port(Passive())
        self.thr = self.Port(Passive())
        self.disch = self.Port(Passive())
        self.ctrl = self.Port(Passive())
        self.reset = self.Port(Passive())

    @override
    def contents(self) -> None:
        super().contents()
        self.footprint(
            'U', 'Package_DIP:DIP-8_W7.62mm',
            {
                '1': self.gnd,
                '2': self.trig,
                '3': self.out,
                '4': self.reset,
                '5': self.ctrl,
                '6': self.thr,
                '7': self.disch,
                '8': self.vcc,
            },
            mfr='Texas Instruments', part='TLC555CDR',
            datasheet='https://www.ti.com/lit/ds/symlink/tlc555.pdf'
        )


class Tlc555Astable(Block):
    """555 timer in astable mode with timing components.

    Astable frequency: f = 1.44 / ((RA + 2*RB) * C)
    With RA=33kΩ, RB=56kΩ, C=10µF: f ≈ 0.99 Hz

    Internal topology (net mapping from schematic JSON):
      VCC ── R1(RA) ── DISCH_NODE ── R2(RB) ── RC_NODE
                           │                        │
                        U1.DISCH               U1.TRIG + U1.THR
                                                    │
                                                 C1(timing) ── GND
      U1.CTRL ── C2(filter) ── GND
      U1.RESET ── VCC (tied high)
    """

    def __init__(self) -> None:
        super().__init__()
        self.ic = self.Block(Tlc555_Device())

        self.pwr = self.Port(VoltageSink.empty(), [Power])
        self.gnd = self.Port(Ground.empty(), [Common])
        self.out = self.Port(DigitalSource.empty())

        # Timing components: RA (R1), RB (R2), C_timing (C1)
        self.ra = self.Block(Resistor(resistance=33 * kOhm(tol=0.05)))
        self.rb = self.Block(Resistor(resistance=56 * kOhm(tol=0.05)))
        self.c_timing = self.Block(Capacitor(capacitance=10 * uFarad(tol=0.2),
                                              voltage=9 * Volt(tol=0.2)))

        # Control pin filter capacitor (C2)
        self.c_ctrl = self.Block(Capacitor(capacitance=10 * nFarad(tol=0.2),
                                            voltage=9 * Volt(tol=0.2)))

        # Decoupling capacitor for VCC (C3)
        self.cap_decoup = self.Block(DecouplingCapacitor(capacitance=100 * nFarad(tol=0.2)))

        # === Connections ===

        # N3/VCC: all VCC-connected pins in one connect call
        self.connect(self.pwr, self.ic.vcc, self.cap_decoup.pwr,
                     self.ic.reset.adapt_to(VoltageSink(
                         voltage_limits=(2, 15) * Volt,
                         current_draw=(0, 0) * mAmp
                     )),
                     self.ra.a.adapt_to(VoltageSink(
                         voltage_limits=(0, 15) * Volt,
                         current_draw=(0, 0.5) * mAmp
                     )))

        # N2/GND: all GND-connected pins in one connect call
        self.connect(self.gnd, self.ic.gnd, self.cap_decoup.gnd,
                     self.c_timing.neg.adapt_to(Ground()),
                     self.c_ctrl.neg.adapt_to(Ground()))

        # Output
        self.connect(self.out, self.ic.out)

        # N5/DISCH_NODE: R1 pin 2 -- DISCH -- R2 pin 1
        self.connect(self.ra.b, self.ic.disch, self.rb.a)

        # N4/RC_NODE: R2 pin 2 -- TRIG -- THR -- C1+
        self.connect(self.rb.b, self.ic.trig, self.ic.thr, self.c_timing.pos)

        # N6/CTRL_FILTER: CTRL -- C2 pin 1
        self.connect(self.ic.ctrl, self.c_ctrl.pos)

    @override
    def contents(self) -> None:
        super().contents()


class BatteryProtected(Block):
    """B1: Power input interface with battery connector, reverse polarity
    protection Schottky diode, and bulk supply capacitor.

    Net mapping:
      N1/BAT_RAW_POS: J1.pin1 → D1.anode
      N3/VCC:         D1.cathode → pwr output, C3.pos, C4.pos
      N2/GND:         J1.pin2 → gnd output, C3.neg, C4.neg
    """

    def __init__(self) -> None:
        super().__init__()
        # J1: 2-pin battery connector
        self.conn = self.Block(PassiveConnector(2))

        # D1: Schottky diode for reverse polarity protection
        self.prot_diode = self.Block(Diode(
            reverse_voltage=(0, 9) * Volt,
            current=(0, 20) * mAmp,
            voltage_drop=(0, 0.5) * Volt,
        ))

        # C4: Bulk supply capacitor (10µF)
        self.cap_bulk = self.Block(DecouplingCapacitor(capacitance=10 * uFarad(tol=0.2)))

        # N1/BAT_RAW_POS: J1 pin 1 → D1 anode
        self.connect(self.conn.pins.request('1'), self.prot_diode.anode)

        # N3/VCC: D1 cathode → VoltageSource output + bulk cap
        self.pwr = self.Export(self.prot_diode.cathode.adapt_to(VoltageSource(
            voltage_out=(4.5, 9) * Volt,
            current_limits=(0, 500) * mAmp
        )))
        self.connect(self.cap_bulk.pwr, self.pwr)

        # N2/GND: J1 pin 2 → Ground output + bulk cap
        self.gnd = self.Export(self.conn.pins.request('2').adapt_to(Ground()), [Common])
        self.connect(self.cap_bulk.gnd, self.gnd)

    @override
    def contents(self) -> None:
        super().contents()


class LedBlinker555(SimpleBoardTop):
    """Top-level board: Single LED Blinker from 5V-9V Battery using TLC555.

    System blocks:
      B1: Power Input Interface (battery connector + protection diode + bulk cap)
      B2: Periodic Signal Generator (TLC555 astable + timing components)
      B3: LED Output Stage (current-limiting resistor + LED)
    """

    @override
    def contents(self) -> None:
        super().contents()

        # ===== B1: Power Input Interface =====
        self.bat = self.Block(BatteryProtected())
        self.vcc = self.connect(self.bat.pwr)
        self.gnd_net = self.connect(self.bat.gnd)

        # ===== B2 & B3: Signal Generator and LED Output =====
        with self.implicit_connect(
            ImplicitConnect(self.vcc, [Power]),
            ImplicitConnect(self.gnd_net, [Common]),
        ) as imp:
            # B2: TLC555 astable oscillator block
            self.timer = imp.Block(Tlc555Astable())

            # B3: LED Output Stage
            # IndicatorLed internally creates R3 (current-limiting resistor) + LED1
            (self.led,), _ = self.chain(
                self.timer.out,
                imp.Block(IndicatorLed(Led.Red)))

    @override
    def refinements(self) -> Refinements:
        return super().refinements() + Refinements(
            instance_refinements=[
                (['bat', 'conn'], PinHeader254),
            ],
            instance_values=[],
        )


class LedBlinker555TestCase(unittest.TestCase):
    def test_design(self) -> None:
        compile_board_inplace(LedBlinker555)
