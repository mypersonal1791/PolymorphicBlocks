# PolymorphicBlocks Abstract Block 清单

本文档列出了 PolymorphicBlocks 项目中所有可用于**结构设计**的抽象模块（Abstract Blocks）。

## 目录

- [说明](#说明)
- [使用指南](#使用指南)
- [LLM 自动生成结构设计](#llm-自动生成结构设计)
- [分类清单](#分类清单)
  - [Power Management (电源管理)](#power-management)
  - [Controllers (控制器)](#controllers)
  - [Connectors (连接器)](#connectors)
  - [Sensors (传感器)](#sensors)
  - [Human Interface (人机接口)](#human-interface)
  - [Passive Components (无源器件)](#passive-components)
  - [Active Components (有源器件)](#active-components)
  - [Interfaces (接口转换)](#interfaces)
  - [Filters (滤波器)](#filters)
  - [Protection (保护电路)](#protection)
  - [Other (其他)](#other)

---

## 说明

### 装饰器类型

- **@abstract_block**: 纯抽象类，需要通过 `refinements` 指定具体实现
- **@abstract_block_default**: 有默认实现的抽象类，可以直接使用（会自动使用默认实现）

### 信息说明

- **继承关系**: 显示该类继承自哪些基类（Category）
- **端口 (Ports)**: 该模块定义的接口端口
- **参数 (Parameters)**: 初始化时需要的参数

---

## 使用指南

### 1. 直接使用有默认实现的 Abstract Block

对于带有 `@abstract_block_default` 的类，可以直接实例化：

```python
class MyBoard(SimpleBoardTop):
    def contents(self):
        super().contents()
        # VoltageRegulator 会自动使用 IdealVoltageRegulator 作为默认实现
        self.reg = self.Block(VoltageRegulator(output_voltage=3.3*Volt(tol=0.05)))
        
        # IoController 会自动使用 IdealIoController 作为默认实现
        self.mcu = self.Block(IoController())
```

### 2. 使用 Refinements 指定具体实现

对于纯 `@abstract_block` 或需要替换默认实现的情况：

```python
class MyBoard(SimpleBoardTop):
    def contents(self):
        super().contents()
        # 使用抽象类，稍后通过 refinements 指定具体型号
        self.reg = self.Block(VoltageRegulator(output_voltage=3.3*Volt(tol=0.05)))
        self.mcu = self.Block(IoController())
    
    def refinements(self) -> Refinements:
        return super().refinements() + Refinements(
            instance_refinements=[
                (self.reg, Ldl1117),  # 指定使用 LDL1117 线性稳压器
                (self.mcu, Stm32f103_48),  # 指定使用 STM32F103 MCU
            ]
        )
```

### 3. 结构设计的层次

```
需求分析
    ↓
功能模块识别 (使用 Category: PowerConditioner, Microcontroller, Sensor...)
    ↓
抽象模块选择 (使用 Abstract Block: VoltageRegulator, IoController...)
    ↓
具体实现选择 (使用 Concrete Block: Ldl1117, Stm32f103_48...)
```

---

## LLM 自动生成结构设计

### 推荐流程

LLM 在生成第一级结构设计时，应该：

1. **分析需求** → 识别功能模块
2. **选择 Abstract Block** → 使用本文档中的抽象类
3. **生成结构描述 JSON** → 不涉及具体型号选择

### JSON 格式示例

```json
{
  "design_name": "USB Keyboard",
  "description": "A simple USB keyboard with 3x2 key matrix",
  "modules": [
    {
      "name": "usb",
      "abstract_type": "UsbDeviceConnector",
      "category": "Connector",
      "description": "USB Type-C connector for power and data"
    },
    {
      "name": "reg",
      "abstract_type": "VoltageRegulator",
      "category": "PowerConditioner",
      "params": {
        "output_voltage": "3.3V"
      },
      "description": "3.3V voltage regulator"
    },
    {
      "name": "mcu",
      "abstract_type": "IoController",
      "category": "ProgrammableController",
      "description": "Microcontroller for keyboard scanning"
    },
    {
      "name": "keys",
      "abstract_type": "Switch",
      "category": "HumanInterface",
      "params": {
        "count": 6
      },
      "description": "Tactile switches for key input"
    }
  ],
  "connections": [
    {
      "from": "usb.pwr",
      "to": "reg.pwr_in",
      "description": "USB power to regulator input"
    },
    {
      "from": "reg.pwr_out",
      "to": "mcu.pwr",
      "description": "Regulated 3.3V to MCU"
    },
    {
      "from": "usb.usb",
      "to": "mcu.usb",
      "description": "USB data lines to MCU"
    },
    {
      "from": "keys",
      "to": "mcu.gpio",
      "description": "Key matrix to MCU GPIO"
    }
  ]
}
```

### 关键原则

1. **只使用 Abstract Block 名称**，不要使用具体型号（如 `Ldl1117`, `Stm32f103_48`）
2. **优先使用带默认实现的类** (`@abstract_block_default`)
3. **参数使用通用规格**（如 `3.3V`），不要指定具体容差
4. **连接描述清晰**，说明信号流向

---

## 分类清单

共找到 **143 个 Abstract Blocks**，按功能分类如下：

- Power Management (电源管理): 12 个
- Controllers (控制器): 3 个
- Connectors (连接器): 13 个
- Sensors (传感器): 15 个
- Human Interface (人机接口): 8 个
- Passive Components (无源器件): 7 个
- Active Components (有源器件): 8 个
- Interfaces (接口转换): 10 个
- Filters (滤波器): 3 个
- Protection (保护电路): 2 个
- Other (其他): 62 个

---

## Power Management

### `BldcDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MotorDriver

**说明**: A brushless motor driver, or at least the power stage for one - may be as simple a 3 half-bridges.

**定义位置**: `Categories.py:162`

---

### `BoostConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealBoostConverter`

**继承**: SwitchingVoltageRegulator

**说明**: Step-up switching converter

**定义位置**: `AbstractPowerConverters.py:504`

---

### `BrushedMotorDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MotorDriver

**说明**: A brushed motor driver, or at least the power stage for one.

**定义位置**: `Categories.py:155`

---

### `BuckBoostConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealVoltageRegulator`

**继承**: SwitchingVoltageRegulator

**说明**: Step-up or switch-down switching converter

**定义位置**: `AbstractPowerConverters.py:762`

---

### `BuckConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealBuckConverter`

**继承**: SwitchingVoltageRegulator

**说明**: Step-down switching converter

**定义位置**: `AbstractPowerConverters.py:178`

---

### `HalfBridge`

**类型**: `@abstract_block_default` → 默认实现: `FetHalfBridgeIndependent`

**继承**: PowerConditioner → Block

**说明**: Half bridge circuit with logic-level inputs and current draw calculated from the output node.

**端口**:
- `gnd` (`Ground`)
- `pwr` (`VoltageSink`)
- `out` (`VoltageSource`)
- `pwr_logic` (`VoltageSink`)

**定义位置**: `PowerCircuits.py:19`

---

### `HalfBridgeDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PowerSwitch → Block

**说明**: Half-bridge driver with independent low / high control for driving two NMOS devices,

**参数**:
- `has_boot_diode`: `BoolLike`

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `low_out` (`DigitalSource`)
- `high_pwr` (`VoltageSink`)
- `high_gnd` (`Ground`)
- `high_out` (`DigitalSource`)

**定义位置**: `GateDrivers.py:8`

---

### `LedDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PowerConditioner → Interface

**说明**: Abstract current-regulated high-power LED driver.

**参数**:
- `max_current`: `RangeLike`

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `leda`
- `ledk`

**定义位置**: `AbstractLedDriver.py:8`

---

### `LinearRegulator`

**类型**: `@abstract_block_default` → 默认实现: `IdealLinearRegulator`

**继承**: VoltageRegulator

**说明**: Structural abstract base class for linear regulators, a voltage regulator that can produce some

**定义位置**: `AbstractPowerConverters.py:77`

---

### `MotorDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PowerSwitch

**定义位置**: `Categories.py:150`

---

### `SwitchingVoltageRegulator`

**类型**: `@abstract_block` (需要 refinement)

**继承**: VoltageRegulator

**定义位置**: `AbstractPowerConverters.py:135`

---

### `VoltageRegulator`

**类型**: `@abstract_block_default` → 默认实现: `IdealVoltageRegulator`

**继承**: PowerConditioner

**说明**: Structural abstract base class for DC-DC voltage regulators with shared ground (non-isolated).

**参数**:
- `output_voltage`: `RangeLike`

**端口**:
- `pwr_in` (`VoltageSink`)
- `pwr_out` (`VoltageSource`)
- `gnd` (`Ground`)

**定义位置**: `AbstractPowerConverters.py:16`

---

## Controllers

### `Fpga`

**类型**: `@abstract_block` (需要 refinement)

**继承**: ProgrammableController

**说明**: FPGA with its surrounding application circuit.

**定义位置**: `Categories.py:73`

---

### `IoController`

**类型**: `@abstract_block` (需要 refinement)

**继承**: ProgrammableController → BaseIoController

**说明**: Structural abstract base class for a programmable controller chip (including microcontrollers that take firmware,

**端口**:
- `gnd` (`Ground`)
- `pwr` (`VoltageSink`)

**定义位置**: `IoController.py:217`

---

### `Microcontroller`

**类型**: `@abstract_block` (需要 refinement)

**继承**: ProgrammableController

**说明**: Microcontroller (with embedded-class processor) with its surrounding application circuit.

**定义位置**: `Categories.py:66`

---

## Connectors

### `BananaJack`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Connector

**说明**: Base class for a single terminal 4mm banana jack, such as used on test equipment.

**端口**:
- `port` (`Passive`)

**定义位置**: `AbstractConnector.py:9`

---

### `Battery`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PowerSource

**参数**:
- `voltage`: `RangeLike`
- `current`: `RangeLike`

**端口**:
- `pwr` (`VoltageSource`)
- `gnd` (`Ground`)

**定义位置**: `AbstractDevices.py:6`

---

### `FootprintPassiveConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PassiveConnector → GeneratorBlock → FootprintBlock

**说明**: PassiveConnector that is a footprint and provides some base functionality for generation.

**定义位置**: `PassiveConnector.py:29`

---

### `ProgrammingConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Connector → Testing

**说明**: Programming / debug / JTAG connectors.

**定义位置**: `Categories.py:339`

---

### `RfConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Connector

**说明**: Base class for a RF connector, with a signal and ground. Signal is passive-typed.

**端口**:
- `sig` (`Passive`)
- `gnd`

**定义位置**: `AbstractConnector.py:24`

---

### `SmaConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: RfConnector

**说明**: Base class for a SMA coax connector.

**定义位置**: `AbstractConnector.py:57`

---

### `SmaFConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: SmaConnector

**说明**: Base class for a SMA F connector, socket with external threads.

**定义位置**: `AbstractConnector.py:68`

---

### `SmaMConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: SmaConnector

**说明**: Base class for a SMA M connector, pin with internal threads.

**定义位置**: `AbstractConnector.py:62`

---

### `SwdCortexTargetConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: ProgrammingConnector

**说明**: Programming header with power and SWD (SWCLK/SWDIO/RESET) pins.

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `swd` (`SwdHostPort`)

**定义位置**: `AbstractDebugHeaders.py:8`

---

### `UflConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: RfConnector

**说明**: Base class for a U.FL / IPEX / UMCC connector, miniature RF connector.

**定义位置**: `AbstractConnector.py:52`

---

### `UsbConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Connector

**说明**: USB connector of any generation / type.

**定义位置**: `UsbConnectors.py:7`

---

### `UsbDeviceConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: UsbConnector → PowerSource

**说明**: Abstract base class for a USB 2.0 device-side port connector

**端口**:
- `pwr` (`VoltageSource`)
- `gnd` (`Ground`)
- `usb` (`UsbHostPort`)

**定义位置**: `UsbConnectors.py:27`

---

### `UsbHostConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: UsbConnector

**说明**: Abstract base class for a USB 2.0 device-side port connector

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `usb` (`UsbDevicePort`)

**定义位置**: `UsbConnectors.py:15`

---

## Sensors

### `Accelerometer`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:237`

---

### `Camera`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**说明**: Imaging sensors, including visible / RGB, IR, and thermal.

**定义位置**: `Categories.py:305`

---

### `CurrentSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:232`

---

### `DistanceSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:312`

---

### `EnvironmentalSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:247`

---

### `GasSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: EnvironmentalSensor

**说明**: Sensors measuring gas concentration, including non-particle IAQ, TVOC, eCO2, and CO2 sensors.

**定义位置**: `Categories.py:269`

---

### `Gyroscope`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:242`

---

### `HumiditySensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: EnvironmentalSensor

**定义位置**: `Categories.py:257`

---

### `LightSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:276`

---

### `MagneticSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:281`

---

### `MagneticSwitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MagneticSensor

**说明**: A switch that is activated by a magnetic field, including omnipolar and bipolar devices.

**定义位置**: `Categories.py:286`

---

### `Magnetometer`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MagneticSensor

**说明**: Linear response magnetic field sensor, potentially with multiple axes

**定义位置**: `Categories.py:293`

---

### `Microphone`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Sensor

**定义位置**: `Categories.py:300`

---

### `PressureSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: EnvironmentalSensor

**说明**: Sensors measuring ambient pressure

**定义位置**: `Categories.py:262`

---

### `TemperatureSensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: EnvironmentalSensor

**定义位置**: `Categories.py:252`

---

## Human Interface

### `DigitalDirectionSwitch`

**类型**: `@abstract_block_default` → 默认实现: `DigitalWrapperDirectionSwitch`

**继承**: HumanInterface

**说明**: Wrapper around DirectionSwitch that provides digital ports that are pulled low (to GND) when pressed.

**端口**:
- `gnd` (`Ground`)
- `a` (`DigitalSource`)
- `b` (`DigitalSource`)
- `c` (`DigitalSource`)
- `d` (`DigitalSource`)

**定义位置**: `AbstractSwitch.py:166`

---

### `DigitalRotaryEncoder`

**类型**: `@abstract_block_default` → 默认实现: `DigitalWrapperRotaryEncoder`

**继承**: HumanInterface

**说明**: Wrapper around RotaryEncoder that provides digital ports that are pulled low (to GND) when pressed.

**端口**:
- `gnd` (`Ground`)
- `a` (`DigitalSource`)
- `b` (`DigitalSource`)

**定义位置**: `AbstractSwitch.py:110`

---

### `Display`

**类型**: `@abstract_block` (需要 refinement)

**继承**: HumanInterface

**说明**: Pixel displays.

**定义位置**: `Categories.py:190`

---

### `EInk`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Display

**说明**: E-ink display, which retains the image after power is removed.

**定义位置**: `Categories.py:211`

---

### `IndicatorSinkLed`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Light → Block

**说明**: Abstract part for an low-side-driven ("common anode") indicator LED

**参数**:
- `color`: `LedColorLike`

**端口**:
- `signal` (`DigitalSink`)
- `pwr` (`VoltageSink`)

**定义位置**: `AbstractLed.py:148`

---

### `Lcd`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Display

**说明**: LCD display, where pixels absorb / reflect light, but do not directly emit light (eg, use a backlight, or are transflective).

**定义位置**: `Categories.py:197`

---

### `Light`

**类型**: `@abstract_block` (需要 refinement)

**继承**: HumanInterface

**说明**: Discrete lights.

**定义位置**: `Categories.py:218`

---

### `Oled`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Display

**说明**: OLED display, with the pixel density of an LCD but with infinite contrast and no backlight.

**定义位置**: `Categories.py:204`

---

## Passive Components

### `AluminumCapacitor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Capacitor

**说明**: Abstract base class for aluminum electrolytic capacitors capacitors which provide compact bulk capacitance

**定义位置**: `AbstractCapacitor.py:190`

---

### `Capacitor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: UnpolarizedCapacitor → KiCadInstantiableBlock → HasStandardFootprint

**说明**: Polarized capacitor, which we assume will be the default

**端口**:
- `pos` (`Passive`)
- `neg` (`Passive`)

**定义位置**: `AbstractCapacitor.py:64`

---

### `CeramicCapacitor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Capacitor

**说明**: Abstract base class for ceramic capacitors, which appear more ideal in terms of lower ESP

**定义位置**: `AbstractCapacitor.py:183`

---

### `FerriteBead`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PassiveComponent → KiCadImportableBlock → HasStandardFootprint

**端口**:
- `a` (`Passive`)
- `b` (`Passive`)

**定义位置**: `AbstractFerriteBead.py:13`

---

### `Inductor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PassiveComponent → KiCadImportableBlock → HasStandardFootprint

**参数**:
- `inductance`: `RangeLike`
- `current`: `RangeLike`
- `frequency`: `RangeLike`
- `resistance_dc`: `RangeLike`

**端口**:
- `a` (`Passive`)
- `b` (`Passive`)

**定义位置**: `AbstractInductor.py:13`

---

### `Resistor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PassiveComponent → KiCadInstantiableBlock → HasStandardFootprint

**参数**:
- `resistance`: `RangeLike`
- `power`: `RangeLike`
- `voltage`: `RangeLike`

**端口**:
- `a` (`Passive`)
- `b` (`Passive`)

**定义位置**: `AbstractResistor.py:15`

---

### `UnpolarizedCapacitor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PassiveComponent

**说明**: Base type for a capacitor, that defines its parameters and without ports (since capacitors can be polarized)

**参数**:
- `capacitance`: `RangeLike`
- `voltage`: `RangeLike`

**定义位置**: `AbstractCapacitor.py:17`

---

## Active Components

### `Bjt`

**类型**: `@abstract_block` (需要 refinement)

**继承**: KiCadImportableBlock → DiscreteSemiconductor → HasStandardFootprint

**说明**: Base class for untyped BJTs

**参数**:
- `collector_voltage`: `RangeLike`
- `collector_current`: `RangeLike`

**端口**:
- `base` (`Passive`)
- `collector` (`Passive`)
- `emitter` (`Passive`)

**定义位置**: `AbstractBjt.py:11`

---

### `Diode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: KiCadImportableBlock → BaseDiode

**说明**: Base class for untyped diodes

**参数**:
- `reverse_voltage`: `RangeLike`
- `current`: `RangeLike`

**定义位置**: `AbstractDiodes.py:53`

---

### `Fet`

**类型**: `@abstract_block` (需要 refinement)

**继承**: KiCadImportableBlock → DiscreteSemiconductor → HasStandardFootprint

**说明**: Base class for untyped MOSFETs

**参数**:
- `drain_voltage`: `RangeLike`
- `drain_current`: `RangeLike`

**端口**:
- `source` (`Passive`)
- `drain` (`Passive`)
- `gate` (`Passive`)

**定义位置**: `AbstractFets.py:13`

---

### `Led`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteSemiconductor → HasStandardFootprint

**参数**:
- `color`: `LedColorLike`

**端口**:
- `a` (`Passive`)
- `k` (`Passive`)

**定义位置**: `AbstractLed.py:17`

---

### `RgbLedCommonAnode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteSemiconductor

**端口**:
- `a` (`Passive`)
- `k_red` (`Passive`)
- `k_green` (`Passive`)
- `k_blue` (`Passive`)

**定义位置**: `AbstractLed.py:75`

---

### `SwitchFet`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Fet

**说明**: FET that switches between an off state and on state, not operating in the linear region except for rise/fall time.

**定义位置**: `AbstractFets.py:235`

---

### `TvsDiode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: BaseDiode

**说明**: Base class for TVS diodes with TVS specific parameters

**参数**:
- `working_voltage`: `RangeLike`

**定义位置**: `AbstractTvsDiode.py:9`

---

### `ZenerDiode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: KiCadImportableBlock → BaseDiode → DiscreteSemiconductor

**说明**: Base class for untyped zeners

**参数**:
- `zener_voltage`: `RangeLike`

**定义位置**: `AbstractDiodes.py:137`

---

## Interfaces

### `AnalogSwitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface → KiCadImportableBlock → Block

**说明**: Base class for a n-ported analog switch with passive-typed ports.

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `control_gnd` (`Ground`)
- `control`
- `com` (`Passive`)
- `inputs`

**定义位置**: `AbstractAnalogSwitch.py:10`

---

### `AnalogToDigital`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface

**定义位置**: `Categories.py:102`

---

### `Antenna`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface → Block

**参数**:
- `frequency`: `RangeLike`
- `impedance`: `RangeLike`
- `power`: `RangeLike`

**端口**:
- `a` (`Passive`)
- `gnd` (`Ground`)

**定义位置**: `AbstractAntenna.py:10`

---

### `BitBangAdapter`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface

**说明**: Adapters that break out a structured Bundle to component wires, useful when bit-banging those protocols

**定义位置**: `Categories.py:122`

---

### `CanTransceiver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface → Block

**说明**: Abstract CAN transceiver

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `controller` (`CanTransceiverPort`)
- `can` (`CanDiffPort`)

**定义位置**: `CanTransceiver.py:6`

---

### `DigitalIsolator`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface → GeneratorBlock

**说明**: Multichannel digital isolator, shifts logic signals between different logic voltages

**端口**:
- `pwr_a` (`VoltageSink`)
- `gnd_a` (`Ground`)
- `in_a`
- `out_a`
- `pwr_b` (`VoltageSink`)
- `gnd_b` (`Ground`)
- `in_b`
- `out_b`

**定义位置**: `DigitalIsolator.py:8`

---

### `DigitalToAnalog`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface

**定义位置**: `Categories.py:107`

---

### `IoExpander`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface

**定义位置**: `Categories.py:117`

---

### `SolidStateRelay`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface → Block

**说明**: Base class for solid state relays.

**端口**:
- `leda` (`Passive`)
- `ledk` (`Passive`)
- `feta` (`Passive`)
- `fetb` (`Passive`)

**定义位置**: `AbstractSolidStateRelay.py:12`

---

### `SpeakerDriver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Interface

**定义位置**: `Categories.py:112`

---

## Filters

### `AnalogFilter`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Filter

**说明**: Analog signal conditioning subcircuit.

**定义位置**: `Categories.py:38`

---

### `DigitalFilter`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Filter

**说明**: Digital signal conditioning block.

**定义位置**: `Categories.py:52`

---

### `RfFilter`

**类型**: `@abstract_block` (需要 refinement)

**继承**: AnalogFilter

**说明**: RF signal conditioning subcircuit.

**定义位置**: `Categories.py:45`

---

## Protection

### `CanEsdDiode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Protection → Block

**端口**:
- `gnd` (`Ground`)
- `can` (`CanDiffPort`)

**定义位置**: `CanTransceiver.py:29`

---

### `UsbEsdDiode`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Protection

**端口**:
- `gnd` (`Ground`)
- `usb` (`UsbPassivePort`)

**定义位置**: `UsbConnectors.py:39`

---

## Other

### `Analog`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Analog blocks that don't fit into one of the other categories

**定义位置**: `Categories.py:17`

---

### `BananaSafetyJack`

**类型**: `@abstract_block` (需要 refinement)

**继承**: BananaJack

**说明**: Base class for a single terminal 4mm banana jack supporting a safety sheath,

**定义位置**: `AbstractConnector.py:18`

---

### `BaseIoController`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PinMappable → Block

**说明**: An abstract IO controller block, that takes power input and provides a grab-bag of common IOs.

**端口**:
- `gpio`
- `adc`
- `spi`
- `i2c`
- `uart`
- `usb`

**定义位置**: `IoController.py:14`

---

### `Connector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Connectors, including card sockets.

**定义位置**: `Categories.py:169`

---

### `Crystal`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent → HasStandardFootprint

**参数**:
- `frequency`: `RangeLike`

**端口**:
- `crystal`
- `gnd`

**定义位置**: `AbstractCrystal.py:12`

---

### `DeprecatedBlock`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalBlock

**说明**: Base class for blocks that are deprecated and planned to be removed

**定义位置**: `Categories.py:410`

---

### `DigitalDirectionSwitchCenter`

**类型**: `@abstract_block_default` → 默认实现: `DigitalWrapperDirectionSwitchWithCenter`

**说明**: DigitalRotaryEncoder mixin adding a switch pin.

**端口**:
- `center` (`DigitalSource`)

**定义位置**: `AbstractSwitch.py:201`

---

### `DigitalRotaryEncoderSwitch`

**类型**: `@abstract_block_default` → 默认实现: `DigitalWrapperRotaryEncoderWithSwitch`

**说明**: DigitalRotaryEncoder mixin adding a switch pin.

**端口**:
- `sw` (`DigitalSource`)

**定义位置**: `AbstractSwitch.py:141`

---

### `DirectionSwitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent

**说明**: Directional switch with a, b, c, d (clockwise) switches and common.

**参数**:
- `voltage`: `RangeLike`
- `current`: `RangeLike`

**端口**:
- `a` (`Passive`)
- `b` (`Passive`)
- `c` (`Passive`)
- `d` (`Passive`)
- `com` (`Passive`)

**定义位置**: `AbstractSwitch.py:65`

---

### `DiscreteApplication`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Subcircuit around a single discrete (and usually passive) component.

**定义位置**: `Categories.py:10`

---

### `DiscreteBoostConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealBoostConverter`

**继承**: BoostConverter

**说明**: Category for discrete boost converter subcircuits (as opposed to integrated components)

**定义位置**: `AbstractPowerConverters.py:513`

---

### `DiscreteBuckBoostConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealVoltageRegulator`

**继承**: BuckBoostConverter

**说明**: Category for discrete buck-boost converter subcircuits (as opposed to integrated components)

**定义位置**: `AbstractPowerConverters.py:767`

---

### `DiscreteBuckConverter`

**类型**: `@abstract_block_default` → 默认实现: `IdealBuckConverter`

**继承**: BuckConverter

**说明**: Category for discrete buck converter subcircuits (as opposed to integrated components)

**定义位置**: `AbstractPowerConverters.py:187`

---

### `DiscreteComponent`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalBlock

**说明**: Discrete component that typically provides untyped ports (not to be be used directly), as a component to be used in an application circuit.

**定义位置**: `Categories.py:367`

---

### `DiscreteSemiconductor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent

**说明**: Discrete semiconductor product, eg diodes and FETs, typically used as part of an application circuit.

**定义位置**: `Categories.py:374`

---

### `DummyDevice`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalBlock

**说明**: Non-physical "device" used to affect parameters.

**定义位置**: `Categories.py:388`

---

### `FetHalfBridge`

**类型**: `@abstract_block` (需要 refinement)

**继承**: HalfBridge

**说明**: Implementation of a half-bridge with two NFETs and a gate driver.

**参数**:
- `frequency`: `RangeLike`
- `fet_rds`: `RangeLike`
- `gate_res`: `RangeLike`

**定义位置**: `PowerCircuits.py:49`

---

### `Filter`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Signal conditioning subcircuit.

**定义位置**: `Categories.py:31`

---

### `Fuse`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent → HasStandardFootprint

**参数**:
- `trip_current`: `RangeLike`

**端口**:
- `a`
- `b`

**定义位置**: `AbstractFuse.py:14`

---

### `HalfBridgeIndependent`

**类型**: `@abstract_block_default` → 默认实现: `FetHalfBridgeIndependent`

**端口**:
- `low_ctl` (`DigitalSink`)
- `high_ctl` (`DigitalSink`)

**定义位置**: `PowerCircuits.py:34`

---

### `HalfBridgePwm`

**类型**: `@abstract_block_default` → 默认实现: `FetHalfBridgePwmReset`

**端口**:
- `pwm_ctl` (`DigitalSink`)

**定义位置**: `PowerCircuits.py:42`

---

### `HumanInterface`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Devices for human interface, eg switches, displays, LEDs

**定义位置**: `Categories.py:183`

---

### `IdealModel`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalBlock

**说明**: Ideal model device that can be used as a placeholder to get a design compiling

**定义位置**: `Categories.py:395`

---

### `Interface`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Interface devices, eg CAN transceiver (CAN <-> SPI / I2C interface),

**定义位置**: `Categories.py:94`

---

### `InternalSubcircuit`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalBlock

**说明**: Internal blocks that are primarily an implementation detail or not re-usable

**定义位置**: `Categories.py:360`

---

### `IsolatedCanTransceiver`

**类型**: `@abstract_block` (需要 refinement)

**继承**: CanTransceiver

**端口**:
- `can_pwr` (`VoltageSink`)
- `can_gnd` (`Ground`)

**定义位置**: `CanTransceiver.py:20`

---

### `Jumper`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent → Block

**说明**: A two-ported passive-typed jumper (a disconnect-able connection), though is treated

**端口**:
- `a`
- `b`

**定义位置**: `AbstractJumper.py:8`

---

### `Label`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DeprecatedBlock

**说明**: DEPRECATED: non-circuit footprints should be added in layout as non-schematic items.

**定义位置**: `Categories.py:417`

---

### `Mechanical`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DeprecatedBlock

**说明**: DEPRECATED: non-circuit footprints should be added in layout as non-schematic items.

**定义位置**: `Categories.py:425`

---

### `MechanicalKeyswitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Switch

**说明**: Abstract class (category) for a mechanical keyboard switch, including sockets.

**定义位置**: `AbstractSwitch.py:34`

---

### `Memory`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Memory device (including sockets and card sockets) with its surrounding application circuit.

**定义位置**: `Categories.py:80`

---

### `MultipackDevice`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: A multipack device (e.g., dualpack opamp, quadpack resistor array) which blocks across the design

**定义位置**: `Categories.py:331`

---

### `MultipackOpamp`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MultipackDevice → MultipackBlock

**说明**: Base class for packed opamps - devices that have multiple opamps in a single package,

**定义位置**: `AbstractOpamp.py:39`

---

### `Opamp`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Analog → KiCadInstantiableBlock → Block

**说明**: Base class for opamps. Parameters need to be more restricted in subclasses.

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `inp` (`AnalogSink`)
- `inn` (`AnalogSink`)
- `out` (`AnalogSource`)

**定义位置**: `AbstractOpamp.py:10`

---

### `OpampApplication`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Analog

**说明**: Opamp-based circuits, typically one that perform some function on signals

**定义位置**: `Categories.py:24`

---

### `Oscillator`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteApplication

**说明**: Device that generates a digital clock signal given power.

**参数**:
- `frequency`: `RangeLike`

**端口**:
- `gnd` (`Ground`)
- `pwr` (`VoltageSink`)
- `out` (`DigitalSource`)

**定义位置**: `AbstractOscillator.py:11`

---

### `OscillatorReference`

**类型**: `@abstract_block_default` → 默认实现: `OscillatorCrystal`

**继承**: DiscreteApplication

**参数**:
- `frequency`: `RangeLike`

**端口**:
- `crystal` (`CrystalPort`)
- `gnd` (`Ground`)

**定义位置**: `AbstractCrystal.py:88`

---

### `PartsTablePart`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: An interface mixin for a part that is selected from a table, defining parameters to allow manual part selection

**定义位置**: `PartsTablePart.py:40`

---

### `PassiveComponent`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent

**说明**: Passives components, typically used as part of an application circuit.

**定义位置**: `Categories.py:381`

---

### `PassiveConnector`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent → Block

**说明**: A base Block that is an elastic n-ported connector with passive type.

**参数**:
- `length`: `IntLike`

**端口**:
- `pins`

**定义位置**: `PassiveConnector.py:9`

---

### `PowerConditioner`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Power conditioning circuits that provide a stable and/or safe power supply, eg voltage regulators

**定义位置**: `Categories.py:136`

---

### `PowerSource`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Power sources, including connectors that also supply power.

**定义位置**: `Categories.py:176`

---

### `PowerSwitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Power switching circuits, eg FET switches and motor drivers

**定义位置**: `Categories.py:143`

---

### `PptcFuse`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Fuse

**说明**: PPTC self-resetting fuse

**定义位置**: `AbstractFuse.py:129`

---

### `ProgrammableController`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: General programmable controller.

**定义位置**: `Categories.py:59`

---

### `Protection`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Circuit protection elements, eg TVS diodes, fuses

**定义位置**: `Categories.py:317`

---

### `Radiofrequency`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Radiofrequency devices.

**定义位置**: `Categories.py:129`

---

### `RealtimeClock`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Realtime clock device.

**定义位置**: `Categories.py:87`

---

### `ResistorArray`

**类型**: `@abstract_block` (需要 refinement)

**继承**: MultipackDevice → MultipackBlock → HasStandardFootprint

**说明**: An n-element resistor array, where all resistors have the same resistance and power rating.

**参数**:
- `count`: `IntLike`

**定义位置**: `AbstractResistorArray.py:19`

---

### `RotaryEncoder`

**类型**: `@abstract_block` (需要 refinement)

**继承**: DiscreteComponent

**说明**: Rotary encoder with discrete clicks and a quadrature signal (A/B/Common).

**参数**:
- `voltage`: `RangeLike`
- `current`: `RangeLike`

**端口**:
- `a` (`Passive`)
- `b` (`Passive`)
- `com` (`Passive`)

**定义位置**: `AbstractSwitch.py:39`

---

### `SelectorArea`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PartsTablePart

**说明**: A base mixin that defines a footprint_area range specification for blocks that automatically select parts.

**定义位置**: `SelectorArea.py:11`

---

### `SelectorFootprint`

**类型**: `@abstract_block` (需要 refinement)

**继承**: PartsTablePart

**说明**: Mixin that allows a specified footprint, for Blocks that automatically select a part.

**定义位置**: `PartsTablePart.py:95`

---

### `Sensor`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Any kind of sensor with any interface. Multi-packed sensors may inherit from multiple categories

**定义位置**: `Categories.py:225`

---

### `SpiMemory`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Memory → Block

**说明**: Base class for SPI memory, with acceptable sizes (in bits) as a range.

**参数**:
- `size`: `RangeLike`

**端口**:
- `pwr` (`VoltageSink`)
- `gnd` (`Ground`)
- `spi` (`SpiPeripheral`)
- `cs` (`DigitalSink`)

**定义位置**: `AbstractSpiMemory.py:8`

---

### `SpiMemoryQspi`

**类型**: `@abstract_block` (需要 refinement)

**说明**: SPI memory that also supports QSPI mode (4-line SPI).

**端口**:
- `io2` (`DigitalBidir`)
- `io3` (`DigitalBidir`)

**定义位置**: `AbstractSpiMemory.py:25`

---

### `Switch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: KiCadImportableBlock → DiscreteComponent

**说明**: Two-ported device that closes a circuit when pressed.

**参数**:
- `voltage`: `RangeLike`
- `current`: `RangeLike`

**端口**:
- `sw` (`Passive`)
- `com` (`Passive`)

**定义位置**: `AbstractSwitch.py:10`

---

### `TactileSwitch`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Switch

**说明**: Abstract class (category) for a tactile switch.

**定义位置**: `AbstractSwitch.py:29`

---

### `TestPoint`

**类型**: `@abstract_block` (需要 refinement)

**继承**: InternalSubcircuit → Block

**说明**: Abstract test point that can take a name as a string, used as the footprint value.

**参数**:
- `tp_name`: `StringLike`

**端口**:
- `io`

**定义位置**: `AbstractTestPoint.py:14`

---

### `Testing`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Block

**说明**: Blocks for testing (eg, test points) and programming (eg, programming headers).

**定义位置**: `Categories.py:324`

---

### `TypedJumper`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Testing

**说明**: Jumper with typed ports (eg, VoltageSource-VoltageSink, instead of Passive).

**定义位置**: `Categories.py:353`

---

### `TypedTestPoint`

**类型**: `@abstract_block` (需要 refinement)

**继承**: Testing

**说明**: Test point with a typed port (eg, VoltageSink, instead of Passive).

**定义位置**: `Categories.py:346`

---

### `VoltageReference`

**类型**: `@abstract_block` (需要 refinement)

**继承**: LinearRegulator

**说明**: Voltage reference, generally provides high accuracy but limited current

**定义位置**: `AbstractPowerConverters.py:87`

---
