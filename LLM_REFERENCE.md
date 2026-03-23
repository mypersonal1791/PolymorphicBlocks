# PolymorphicBlocks (EDG) — LLM Code Generation Reference

> This document is a concise, complete reference for generating PolymorphicBlocks HDL code.
> PolymorphicBlocks is a Python-based Hardware Description Language (HDL) for PCB design.
> Users define circuit boards as Python classes; the compiler generates KiCad netlists.

---

## 1. Project Setup & Entry Point

Every design file starts with:

```python
from edg import *

class MyBoard(SimpleBoardTop):          # or JlcBoardTop / BoardTop
    def contents(self) -> None:
        super().contents()
        # instantiate blocks, make connections here

    def refinements(self) -> Refinements:
        return super().refinements() + Refinements(
            instance_refinements=[...],
            instance_values=[...],
            class_refinements=[...],
            class_values=[...],
        )

if __name__ == "__main__":
    compile_board_inplace(MyBoard)
```

### Top-Level Base Classes (choose one)

| Class | Description |
|---|---|
| `SimpleBoardTop` | Easiest to start; includes JLC parts + relaxed settings (e.g. ignores inductor frequency) |
| `JlcBoardTop` | Uses JLC assembly parts + adds tooling holes |
| `BoardTop` | Generic SMD hand-solderable defaults; no JLC-specific parts |

---

## 2. Core Concepts

### 2.1 Blocks

**Blocks** are the fundamental unit — they represent subcircuits (hierarchy sheets).

- **`Block`** — a subcircuit with ports, sub-blocks, and connections.
- **`FootprintBlock`** — a Block tied to a single PCB footprint (like a schematic symbol).
- **`GeneratorBlock`** — a Block whose contents are generated at compile time based on solved parameter values.
- **`KiCadSchematicBlock`** — a Block whose implementation is imported from a KiCad `.kicad_sch` file.

### 2.2 Ports

Ports define the electrical interface of a Block. They are strongly typed and carry electrical parameters (voltage limits, current draw, thresholds, etc.).

### 2.3 Links

Links define how connected ports propagate parameters and check constraints. Links are **automatically inferred** from port types — you never create them manually.

### 2.4 Parameters

Variables attached to blocks/ports. Types: `BoolExpr`, `IntExpr`, `FloatExpr`, `RangeExpr`, `StringExpr`. The compiler solves parameter values; in HDL code you work with expressions, not concrete values.

### 2.5 Refinements

A top-level mechanism to substitute abstract blocks with concrete implementations, or to force parameter values.

---

## 3. Block Definition Patterns

### 3.1 Basic Block (subcircuit wrapper)

```python
class MySensor(Block):
    def __init__(self) -> None:
        super().__init__()
        self.ic = self.Block(MySensor_Device())       # internal footprint block
        self.pwr = self.Export(self.ic.vcc, [Power])   # export ports with tags
        self.gnd = self.Export(self.ic.gnd, [Common])
        self.out = self.Export(self.ic.vout)

        self.cap = self.Block(DecouplingCapacitor(capacitance=0.1*uFarad(tol=0.2)))
        self.connect(self.cap.pwr, self.pwr)
        self.connect(self.cap.gnd, self.gnd)

    def contents(self) -> None:
        super().contents()
```

### 3.2 FootprintBlock (component with PCB footprint)

```python
class MySensor_Device(FootprintBlock):
    def __init__(self) -> None:
        super().__init__()
        self.vcc = self.Port(VoltageSink(
            voltage_limits=(1.8, 5.5)*Volt,
            current_draw=(0.5, 2.0)*uAmp))
        self.gnd = self.Port(Ground())
        self.vout = self.Port(DigitalSource.from_supply(
            self.gnd, self.vcc,
            current_limits=(-9, 9)*mAmp,
            output_threshold_offset=(0.2, -0.3)))

    def contents(self) -> None:
        super().contents()
        self.footprint(
            'U', 'Package_TO_SOT_SMD:SOT-23',
            {'1': self.vcc, '2': self.vout, '3': self.gnd},
            mfr='Manufacturer', part='PartNumber',
            datasheet='https://...')
```

### 3.3 GeneratorBlock (parameterized, dynamic circuit)

```python
class LedArray(GeneratorBlock):
    @init_in_parent
    def __init__(self, count: IntLike) -> None:
        super().__init__()
        self.ios = self.Port(Vector(DigitalSink.empty()), [Input])
        self.gnd = self.Port(Ground.empty(), [Common])
        self.count = self.ArgParameter(count)
        self.generator_param(self.count)

    def generate(self) -> None:
        super().generate()
        self.led = ElementDict[IndicatorLed]()
        for i in range(self.get(self.count)):
            io = self.ios.append_elt(DigitalSink.empty())
            self.led[i] = self.Block(IndicatorLed())
            self.connect(io, self.led[i].signal)
            self.connect(self.gnd, self.led[i].gnd)
```

### 3.4 KiCadSchematicBlock (schematic-imported)

```python
class Hx711(KiCadSchematicBlock):
    def __init__(self) -> None:
        super().__init__()
        self.pwr = self.Port(VoltageSink.empty(), [Power])
        self.gnd = self.Port(Ground.empty(), [Common])
        self.dout = self.Port(DigitalSource.empty())
        self.sck = self.Port(DigitalSink.empty())

    def contents(self) -> None:
        super().contents()
        self.import_kicad(
            self.file_path("resources", "Hx711.kicad_sch"),
            auto_adapt=True)
```

---

## 4. Port Types Reference

### 4.1 Single-Wire Ports

| Port Type | Role | Key Parameters |
|---|---|---|
| `VoltageSource(voltage_out, current_limits)` | Power output | `voltage_out`: Range, `current_limits`: Range |
| `VoltageSink(voltage_limits, current_draw)` | Power input | `voltage_limits`: Range, `current_draw`: Range |
| `Ground()` | Ground reference | Convenience for ground VoltageSink |
| `DigitalSource(voltage_out, current_limits, output_thresholds)` | Digital output | |
| `DigitalSink(voltage_limits, current_draw, input_thresholds)` | Digital input | |
| `DigitalBidir(...)` | Bidirectional GPIO | Has all args of Source + Sink |
| `AnalogSource(voltage_out, current_limits, impedance)` | Analog output | |
| `AnalogSink(voltage_limits, current_draw, impedance)` | Analog input | |
| `Passive()` | Untyped copper wire | Can be adapted to typed ports via `.adapt_to(...)` |

### 4.2 Bundle Ports (multi-signal)

| Port Type | Signals | Usage |
|---|---|---|
| `I2cController` / `I2cTarget` | `.scl`, `.sda` | I2C bus |
| `SpiController` / `SpiPeripheral` | `.sck`, `.miso`, `.mosi` | SPI bus (CS separate) |
| `UartPort` | `.tx`, `.rx` | UART (crossover) |
| `UsbHostPort` / `UsbDevicePort` | `.dp`, `.dm` | USB data |
| `CanControllerPort` / `CanTransceiverPort` | `.txd`, `.rxd` | CAN logic-level |
| `CanDiffPort` | `.canh`, `.canl` | CAN differential bus |
| `SwdHostPort` / `SwdTargetPort` | `.swdio`, `.swclk`, `.swo`, `.reset` | SWD debug |
| `CrystalDriver` / `CrystalPort` | `.xi`, `.xo` | Crystal oscillator |

### 4.3 Convenience Constructors

```python
DigitalSource.from_supply(gnd_port, pwr_port,
    current_limits=..., output_threshold_offset=(low_offset, high_offset))
DigitalSink.from_supply(gnd_port, pwr_port, ...)
DigitalSource.low_from_supply(gnd_port)     # open-drain low-side
DigitalSource.pullup_from_supply(pwr_port)  # pull-up source
```

### 4.4 Port Tags (for implicit connections)

| Tag | Meaning |
|---|---|
| `[Power]` | Positive voltage rail |
| `[Common]` | Ground |
| `[Input]` | Signal input (for chain) |
| `[Output]` | Signal output (for chain) |
| `[InOut]` | Bidirectional signal (for chain) |

### 4.5 `.empty()` Ports

Use `.empty()` when defining **intermediate** (wrapper/export) ports that will inherit parameters from internal connections:

```python
self.pwr = self.Port(VoltageSink.empty(), [Power])
self.gnd = self.Port(Ground.empty(), [Common])
self.out = self.Port(DigitalSource.empty())
```

---

## 5. Units

All electrical values use unit constructors that create `Range` values:

```python
# Voltage
3.3*Volt(tol=0.05)       # 3.3V ± 5% → Range(3.135, 3.465)
(1.8, 5.5)*Volt           # explicit range 1.8V to 5.5V
12*Volt(tol=0.1)          # 12V ± 10%

# Current
(0, 500)*mAmp             # 0 to 500mA
(0.5, 2.0)*uAmp           # 0.5 to 2.0µA

# Resistance
10*kOhm(tol=0.05)         # 10kΩ ± 5%
4.7*kOhm(tol=0.01)        # 4.7kΩ ± 1%
(1, 10)*kOhm              # 1kΩ to 10kΩ range

# Capacitance
0.1*uFarad(tol=0.2)       # 0.1µF ± 20%
10*uFarad(tol=0.2)        # 10µF ± 20%

# Inductance
uHenry, nHenry, Henry

# Frequency
kHertz, MHertz, GHertz

# Other
Ohm, mOhm, MOhm
Amp, nAmp, pAmp
Watt, mVolt
```

The `Range` class also has utilities:
```python
Range.all()                # (-inf, inf)
Range.from_lower(4.0)     # [4.0, inf)
Range(low, high)           # explicit range
```

---

## 6. Top-Level Design Operations

### 6.1 Block Instantiation

```python
self.usb = self.Block(UsbCReceptacle())
self.reg = self.Block(VoltageRegulator(3.3*Volt(tol=0.05)))
self.mcu = self.Block(IoController())
```

### 6.2 Connect

```python
self.connect(self.usb.gnd, self.reg.gnd, self.mcu.gnd)  # multi-port connect
self.connect(self.usb.pwr, self.reg.pwr_in)
self.connect(self.reg.pwr_out, self.mcu.pwr)
```

### 6.3 Named Connections (net names)

```python
self.v3v3 = self.connect(self.reg.pwr_out)
self.gnd = self.connect(self.usb.gnd)
# Then use self.v3v3 and self.gnd in implicit_connect or further connects
```

### 6.4 Implicit Connections

Automatically connect `Power`/`Common`-tagged ports of blocks instantiated with `imp.Block(...)`:

```python
with self.implicit_connect(
    ImplicitConnect(self.reg.pwr_out, [Power]),
    ImplicitConnect(self.reg.gnd, [Common]),
) as imp:
    self.mcu = imp.Block(IoController())        # pwr and gnd auto-connected
    self.led = imp.Block(IndicatorLed())         # pwr and gnd auto-connected
    self.connect(self.mcu.gpio.request('led'), self.led.signal)  # still need signal connections
```

### 6.5 Chain Connections

Chain connects blocks in sequence from left (output) to right (input):

```python
(self.sw, ), _ = self.chain(
    imp.Block(DigitalSwitch()),
    self.mcu.gpio.request('sw'))

(self.led, ), _ = self.chain(
    self.mcu.gpio.request('led'),
    imp.Block(IndicatorLed()))

# More complex chain with multiple blocks
(self.reg_5v, self.tp_5v, self.prot_5v), _ = self.chain(
    self.v12,
    imp.Block(VoltageRegulator(output_voltage=4*Volt(tol=0.05))),
    self.Block(VoltageTestPoint()),
    imp.Block(ProtectionZenerDiode(voltage=(5.5, 6.8)*Volt)))
```

### 6.6 Port Arrays (dynamic IO)

Requesting individual ports from a port array:
```python
self.mcu.gpio.request('led')          # request single GPIO with name
self.mcu.gpio.request()               # request unnamed GPIO
self.mcu.adc.request('sensor')        # request ADC pin
self.mcu.with_mixin(IoControllerCan()).can.request('can')  # request CAN peripheral
```

Requesting a sub-array:
```python
self.mcu.gpio.request_vector('leds')  # request a vector of GPIOs
self.connect(self.mcu.gpio.request_vector('led'), self.led_array.ios)
```

### 6.7 ElementDict (arraying blocks)

```python
self.led = ElementDict[IndicatorLed]()
for i in range(4):
    self.led[i] = imp.Block(IndicatorLed())
    self.connect(self.mcu.gpio.request(f'led{i}'), self.led[i].signal)
```

### 6.8 Export (forwarding inner ports)

```python
self.pwr = self.Export(self.ic.vcc, [Power])      # export with tag
self.gnd = self.Export(self.ic.gnd, [Common])
self.out = self.Export(self.ic.vout)               # export without tag
```

### 6.9 `.connected()` Shorthand

Some blocks provide a `.connected(...)` convenience method:

```python
self.tp_pwr = self.Block(VoltageTestPoint()).connected(self.pwr.pwr)
self.tp_gnd = self.Block(GroundTestPoint()).connected(self.pwr.gnd)
```

### 6.10 Mixins (extending IoController interfaces)

```python
self.mcu = imp.Block(IoController())
self.mcu.with_mixin(IoControllerWifi())      # add WiFi capability
self.mcu.with_mixin(IoControllerBle())       # add BLE capability
mcu_usb = self.mcu.with_mixin(IoControllerUsb())
mcu_can = self.mcu.with_mixin(IoControllerCan())
mcu_dac = self.mcu.with_mixin(IoControllerDac())
mcu_pwr = self.mcu.with_mixin(IoControllerPowerOut())
mcu_usb_out = self.mcu.with_mixin(IoControllerUsbOut())

# Then use the mixin's ports:
self.connect(self.usb.usb, mcu_usb.usb.request())
mcu_can.can.request('can')
mcu_dac.dac.request('spk')
```

### 6.11 Port Adapters

`Passive` ports can be adapted to typed ports:
```python
self.conn = self.Block(PassiveConnector(4))
self.conn.pins.request('1').adapt_to(DigitalSink())
self.conn.pins.request('2').adapt_to(DigitalSource())
self.conn.pins.request('3').adapt_to(Ground())
self.conn.pins.request('4').adapt_to(VoltageSink(current_draw=(0, 0)*mAmp))
```

Voltage ports can also be adapted:
```python
driver.output.as_digital_source()  # VoltageSource → DigitalSource
port.as_ground(current_draw=...)   # VoltageSink → GroundReference
port.as_analog_source()            # VoltageSink → AnalogSource
```

---

## 7. Refinements System

Refinements are defined in the top-level design's `refinements()` method:

```python
def refinements(self) -> Refinements:
    return super().refinements() + Refinements(
        # Replace a specific block instance with a concrete class
        instance_refinements=[
            (['reg'], Tps561201),          # refine block at path 'reg'
            (['mcu'], Esp32_Wroom_32),     # refine block at path 'mcu'
        ],
        # Force parameter values on specific instances
        instance_values=[
            (['mcu', 'pin_assigns'], ['led0=26', 'led1=27']),
            (['mcu', 'programming'], 'uart-auto'),
            (['refdes_prefix'], 'F'),
        ],
        # Replace ALL instances of an abstract class design-wide
        class_refinements=[
            (Switch, KailhSocket),          # all Switch → KailhSocket
            (TestPoint, CompactKeystone5015),
            (EspProgrammingHeader, EspProgrammingTc2030),
        ],
        # Set parameter values on all instances of a class
        class_values=[
            (Esp32c3, ['not_recommended'], True),
            (CompactKeystone5015, ['lcsc_part'], 'C5199798'),
        ],
    )
```

### Pin Assignment

```python
instance_values=[
    (['mcu', 'pin_assigns'], [
        'led0=26',            # assign by footprint pin number
        'led1=27',
        'spi.sck=GPIO18',    # assign by pin name
        'rgb=_GPIO2_STRAP_EXT_PU',  # force strapping pin
    ]),
]
```

### ParamValue (cross-reference)

```python
instance_values=[
    (['fan_drv[0]', 'drv', 'footprint_spec'], 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'),
    (['fan_drv[1]', 'drv', 'footprint_spec'],
        ParamValue(['fan_drv[0]', 'drv', 'footprint_spec'])),  # copy from another instance
]
```

---

## 8. Common Library Blocks

### 8.1 Power

| Block | Description | Key Parameters |
|---|---|---|
| `VoltageRegulator(output_voltage)` | Abstract voltage regulator | `output_voltage`: e.g. `3.3*Volt(tol=0.05)` |
| `LinearRegulator(output_voltage)` | Abstract LDO | Same |
| `BuckConverter(output_voltage)` | Abstract buck converter | Same |
| `BoostConverter(output_voltage)` | Abstract boost converter | Same |
| `PowerBarrelJack(voltage_out, current_limits)` | DC barrel jack | |
| `ProtectionZenerDiode(voltage)` | Overvoltage protection | `voltage`: e.g. `(3.45, 3.9)*Volt` |

Concrete implementations (used in `instance_refinements`):
`Tps561201`, `Tps54202h`, `Ap2204k`, `Ap7215`, `Ldl1117`, `Ap3012`, etc.

### 8.2 Connectors & USB

| Block | Description |
|---|---|
| `UsbCReceptacle()` | USB-C connector; ports: `.pwr`, `.gnd`, `.usb` |
| `PassiveConnector(pin_count)` | Generic pin header; ports: `.pins` (port array of `Passive`) |
| `UsbEsdDiode()` | USB ESD protection |

### 8.3 Microcontrollers & IoController

`IoController()` is the abstract microcontroller. Common port arrays:
- `.gpio` — general purpose IO
- `.adc` — analog inputs
- `.spi` — SPI controllers
- `.i2c` — I2C controllers
- `.uart` — UART ports
- `.pwr` — power input
- `.gnd` — ground

Concrete MCUs (used in `instance_refinements`):
`Stm32f103_48`, `Esp32_Wroom_32`, `Esp32c3`, `Esp32c3_Wroom02`, `Esp32s3_Wroom_1`,
`Nucleo_F303k8`, `Xiao_Rp2040`, etc.

### 8.4 Indicators & Switches

| Block | Description |
|---|---|
| `IndicatorLed(color?)` | LED with auto-sized resistor; ports: `.signal`, `.gnd` |
| `IndicatorSinkLed(color?)` | Active-low LED; ports: `.signal`, `.gnd` |
| `IndicatorSinkRgbLed()` | RGB LED; ports: `.signals` (vector), `.gnd` |
| `DigitalSwitch()` | Tactile switch with pull; ports: `.out`, `.gnd` |
| `DigitalRotaryEncoder()` | Rotary encoder; ports: `.a`, `.b` |

LED colors: `Led.Red`, `Led.Green`, `Led.Blue`, `Led.White`, `Led.Yellow`, etc.

### 8.5 Passive Components

| Block | Description |
|---|---|
| `Resistor` | Abstract resistor (auto-selected from parts table) |
| `Capacitor` | Abstract capacitor (auto-selected) |
| `Inductor` | Abstract inductor |
| `DecouplingCapacitor(capacitance)` | Decoupling cap with auto power connection |
| `PullupResistor(resistance)` | Pull-up resistor; ports: `.pwr`, `.io` |
| `PulldownResistor(resistance)` | Pull-down resistor; ports: `.gnd`, `.io` |
| `SeriesPowerResistor(resistance)` | Series power resistor |
| `FerriteBead` / `SeriesPowerFerriteBead()` | Ferrite bead |

### 8.6 Analog / Signal Processing

| Block | Description |
|---|---|
| `VoltageSenseDivider(full_scale_voltage, impedance)` | Voltage divider for ADC sensing |
| `VoltageDivider(output_voltage, impedance)` | Voltage divider |
| `FeedbackVoltageDivider(...)` | For voltage regulator feedback |
| `LowPassRc(impedance, cutoff_freq)` | RC low-pass filter |
| `Amplifier(amplification, impedance)` | Op-amp based amplifier |
| `OpampFollower()` | Unity-gain buffer |
| `VoltageComparator(...)` | Voltage comparator circuit |

### 8.7 Communication Interfaces

| Block | Description |
|---|---|
| `CanTransceiver()` | CAN bus transceiver; ports: `.controller`, `.can` |
| `I2cPullup()` | I2C pull-up resistors |
| `UsbBitBang()` | USB bit-bang implementation |
| `Cp2102()` | USB-to-UART converter |
| `DigitalIsolator()` | Digital isolator |

### 8.8 Drivers & Switches

| Block | Description |
|---|---|
| `HighSideSwitch(pull_resistance, max_rds)` | High-side FET switch; ports: `.control`, `.output` |
| `OpenDrainDriver()` | Open-drain driver |
| `HalfBridge(...)` | Half-bridge driver |
| `NeopixelArray(count)` | WS2812/SK6805 LED strip |

### 8.9 Testing & Debug

| Block | Description |
|---|---|
| `VoltageTestPoint()` | Voltage test point; `.connected(port)` shorthand |
| `GroundTestPoint()` | Ground test point |
| `DigitalTestPoint()` | Digital test point |
| `AnalogTestPoint()` | Analog test point |
| `SwdCortexTargetConnector()` | SWD debug header |

### 8.10 Miscellaneous

| Block | Description |
|---|---|
| `Speaker()` | Speaker connector |
| `AaBatteryStack(count)` | AA battery stack |
| `CpuFanConnector()` | PC fan connector |
| `SwitchMatrix(nrows, ncols)` | Switch matrix |

---

## 9. `__init__` vs `contents` Split

- **`__init__`**: Define the block's **interface** — ports, parameters, exports, and sub-blocks needed for exports.
- **`contents`**: Define the block's **implementation** — sub-blocks, connections, constraints, footprints.

This split enables the compiler to inspect interfaces without building full trees. Both must call `super().__init__()` / `super().contents()`.

For `GeneratorBlock`, the generator function replaces `contents`:
- **`__init__`**: Define ports, parameters, register generator with `self.generator_param(...)`.
- **`generate`**: Called with solved parameter values; create sub-blocks & connections.

---

## 10. Key Rules & Gotchas

1. **Always call `super().contents()`** (and `super().__init__()`) at the start of overridden methods.

2. **All blocks must be assigned to `self.*`** for naming:
   ```python
   self.led = self.Block(IndicatorLed())    # ✓ correct
   led = self.Block(IndicatorLed())          # ✗ no name assigned
   ```

3. **Intermediate/wrapper ports must use `.empty()`** to avoid double-assignment of parameters.

4. **`@init_in_parent` decorator** is required when a Block's `__init__` takes parameter arguments (like `IntLike`, `RangeLike`).

5. **Abstract blocks** (`VoltageRegulator`, `IoController`, `Resistor`, etc.) must be refined to concrete implementations via `refinements()`.

6. **Port arrays** (`.gpio`, `.adc`, `.spi`, etc.) require `.request('name')` for individual ports or `.request_vector('name')` for sub-arrays.

7. **Implicit connections** only apply to blocks instantiated with `imp.Block(...)`, not `self.Block(...)`.

8. **`self.connect(...)` can take named connections** (returned `Connection` objects) as arguments:
   ```python
   self.v3v3 = self.connect(self.reg.pwr_out)
   # later:
   ImplicitConnect(self.v3v3, [Power])
   ```

9. **Tolerance** is required for component values:
   ```python
   10*kOhm(tol=0.05)       # ✓ correct: 10kΩ ± 5%
   10*kOhm                  # ✗ missing tolerance
   ```

10. **`ElementDict`** is needed for arrays of blocks:
    ```python
    self.led = ElementDict[IndicatorLed]()
    for i in range(4):
        self.led[i] = self.Block(IndicatorLed())
    ```

11. **`chain` direction**: left (output/source) → right (input/sink). Returns `(tuple_of_blocks,), chain_obj`:
    ```python
    (self.block1, self.block2), _ = self.chain(source_port, imp.Block(A()), imp.Block(B()))
    ```

12. **Multipack** (optional optimization) combines multiple components into one physical package:
    ```python
    def multipack(self) -> None:
        self.res_pack = self.PackedBlock(ResistorArray())
        self.pack(self.res_pack.elements.request('0'), ['led', 'led[0]', 'res'])
    ```

---

## 11. Complete Examples

### Example 1: Simple Blinky Board

```python
from edg import *

class BlinkyBoard(SimpleBoardTop):
    def contents(self) -> None:
        super().contents()
        self.usb = self.Block(UsbCReceptacle())
        self.reg = self.Block(VoltageRegulator(3.3*Volt(tol=0.05)))
        self.connect(self.usb.gnd, self.reg.gnd)
        self.connect(self.usb.pwr, self.reg.pwr_in)

        with self.implicit_connect(
            ImplicitConnect(self.reg.pwr_out, [Power]),
            ImplicitConnect(self.reg.gnd, [Common]),
        ) as imp:
            self.mcu = imp.Block(IoController())
            (self.sw, ), _ = self.chain(
                imp.Block(DigitalSwitch()), self.mcu.gpio.request('sw'))
            self.led = ElementDict[IndicatorLed]()
            for i in range(4):
                (self.led[i], ), _ = self.chain(
                    self.mcu.gpio.request(f'led{i}'), imp.Block(IndicatorLed()))

    def refinements(self) -> Refinements:
        return super().refinements() + Refinements(
            instance_refinements=[
                (['reg'], Tps561201),
                (['mcu'], Esp32_Wroom_32),
            ],
            instance_values=[
                (['mcu', 'pin_assigns'], [
                    'led0=26', 'led1=27', 'led2=28', 'led3=29',
                ]),
            ])

if __name__ == "__main__":
    compile_board_inplace(BlinkyBoard)
```

### Example 2: IoT Fan Controller (multi-domain power)

```python
from edg import *

class IotFan(JlcBoardTop):
    def contents(self) -> None:
        super().contents()
        self.pwr = self.Block(PowerBarrelJack(
            voltage_out=12*Volt(tol=0.05), current_limits=(0, 5)*Amp))
        self.v12 = self.connect(self.pwr.pwr)
        self.gnd = self.connect(self.pwr.gnd)

        with self.implicit_connect(
            ImplicitConnect(self.gnd, [Common]),
        ) as imp:
            (self.reg_5v, ), _ = self.chain(
                self.v12,
                imp.Block(VoltageRegulator(output_voltage=4*Volt(tol=0.05))))
            self.v5 = self.connect(self.reg_5v.pwr_out)

            (self.reg_3v3, ), _ = self.chain(
                self.v5,
                imp.Block(VoltageRegulator(output_voltage=3.3*Volt(tol=0.05))))
            self.v3v3 = self.connect(self.reg_3v3.pwr_out)

        with self.implicit_connect(
            ImplicitConnect(self.v3v3, [Power]),
            ImplicitConnect(self.gnd, [Common]),
        ) as imp:
            self.mcu = imp.Block(IoController())
            self.mcu.with_mixin(IoControllerWifi())

            (self.ledr, ), _ = self.chain(
                imp.Block(IndicatorSinkLed(Led.Red)),
                self.mcu.gpio.request('led'))

    def refinements(self) -> Refinements:
        return super().refinements() + Refinements(
            instance_refinements=[
                (['mcu'], Esp32c3),
                (['reg_5v'], Tps54202h),
                (['reg_3v3'], Ap7215),
            ],
            instance_values=[
                (['mcu', 'programming'], 'uart-auto'),
            ])

if __name__ == "__main__":
    compile_board_inplace(IotFan)
```

### Example 3: Custom FootprintBlock + Wrapper

```python
from edg import *

class MyChip_Device(FootprintBlock):
    def __init__(self) -> None:
        super().__init__()
        self.vcc = self.Port(VoltageSink(
            voltage_limits=(2.7, 5.5)*Volt,
            current_draw=(1, 10)*mAmp))
        self.gnd = self.Port(Ground())
        self.sda = self.Port(DigitalBidir.from_supply(
            self.gnd, self.vcc,
            current_limits=(-3, 3)*mAmp))
        self.scl = self.Port(DigitalSink.from_supply(
            self.gnd, self.vcc))

    def contents(self) -> None:
        super().contents()
        self.footprint(
            'U', 'Package_TO_SOT_SMD:SOT-23-5',
            {'1': self.vcc, '2': self.gnd, '3': self.scl,
             '4': self.sda, '5': self.gnd},
            mfr='Example', part='MYCHIP001')

class MyChip(Block):
    def __init__(self) -> None:
        super().__init__()
        self.ic = self.Block(MyChip_Device())
        self.pwr = self.Export(self.ic.vcc, [Power])
        self.gnd = self.Export(self.ic.gnd, [Common])
        self.i2c = self.Port(I2cTarget.empty())

        self.connect(self.ic.sda, self.i2c.sda)
        self.connect(self.ic.scl, self.i2c.scl)

        self.cap = self.Block(DecouplingCapacitor(capacitance=0.1*uFarad(tol=0.2)))
        self.connect(self.cap.pwr, self.pwr)
        self.connect(self.cap.gnd, self.gnd)

    def contents(self) -> None:
        super().contents()
```

---

## 12. Design Pattern Summary

| Pattern | When to Use |
|---|---|
| `SimpleBoardTop` | Top-level board, getting started |
| `JlcBoardTop` | Production board for JLC assembly |
| `Block` | Subcircuit wrapper with ports |
| `FootprintBlock` | Physical component with footprint |
| `GeneratorBlock` | Parameterized circuit (dynamic count, etc.) |
| `KiCadSchematicBlock` | Complex analog circuit from KiCad schematic |
| `self.Block(...)` | Instantiate sub-block (no implicit connections) |
| `imp.Block(...)` | Instantiate with implicit power/ground |
| `self.Export(...)` | Forward inner port to block boundary |
| `self.connect(...)` | Connect ports together |
| `self.chain(...)` | Chain-connect blocks in sequence |
| `ElementDict[T]()` | Array of blocks |
| `Vector(PortType.empty())` | Dynamic-size port array |
| `@init_in_parent` | Required for parameterized Block constructors |
| `refinements()` | Substitute abstract→concrete, set values |
