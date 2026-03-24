对，IR 该改了。
现在最合适的做法是把第 1 步的 IR 从：

* **模块 + PB 端口级 connections**

改成：

* **模块 + 架构级 relations**

因为你现在的 registry 对 top-level structural design 足够支持“模块选择”和“粗粒度关系判断”，但并不足够支持端口级连接。比如 `UsbDeviceConnector` 和 `VoltageRegulator` 有显式端口，而 `Microcontroller` 没有 `o`，只有 `IoController` 暴露了 `gnd / pwr`，这正说明第 1 步不该要求所有块都落到 PB 端口级连接。 

下面我直接给出**修改后的 IR schema**。

---

# 新版 IR：`pb_arch_v1`

这是**第 1 步结构设计专用 schema**。
目标是模仿人类做系统结构设计的方式：

* 先定模块
* 再定模块之间的架构关系
* 不直接落到 PB 端口级 `connect(...)`

---

## 1）完整 schema 结构

```json
{
  "ir_version": "pb_arch_v1",
  "system": {
    "name": "string",
    "goal": "string",
    "design_stage": "architecture"
  },
  "requirements": {
    "functional": ["string"],
    "constraints": [
      {
        "key": "string",
        "value": "string | number | boolean"
      }
    ]
  },
  "blocks": [
    {
      "id": "string",
      "pb_class": "string",
      "class_source": "registry | generated_composite",
      "tier": "sys | sub | func",
      "role": "string",
      "params": {},
      "notes": "string"
    }
  ],
  "relations": [
    {
      "from": "block_id",
      "to": "block_id",
      "type": "power_flow | data_path | control_path | sensing_path | user_input_path | protection_path | clock_path | storage_path | generic_interface",
      "intent": "string",
      "required": true
    }
  ],
  "open_issues": [
    {
      "type": "string",
      "target": "string",
      "reason": "string"
    }
  ],
  "validation_targets": {
    "must_use_registry_classes": true,
    "must_respect_tier_policy": true,
    "must_cover_all_functional_requirements": true,
    "must_not_use_port_level_connections": true
  }
}
```

---

## 2）字段解释

### `system`

定义这个 IR 的任务边界。
这里固定加上：

```json
"design_stage": "architecture"
```

作用是明确告诉 agent：

> 这是结构设计，不是 PB 代码生成，不是 refinement，不是原理图级连接。

---

### `requirements`

这部分不变。
它主要服务于多 agent 评审，检查“需求是否被结构承接”。

---

### `blocks`

这是模块层，不再要求所有块都必须有可连接端口。
因为当前 registry 里很多 top-level block 只有名称、简介和 tier，没有完整 `o`。例如 `Microcontroller` 只有语义标签，没有显式 ports，而 `IoController` 至少有 `gnd / pwr`。

#### 字段定义

* `id`：实例名
* `pb_class`：来自 registry 的 block 名
* `class_source`：

  * `registry`
  * `generated_composite`
* `tier`：直接继承 registry
* `role`：这个模块在当前系统里的职责
* `params`：结构设计阶段可见参数
* `notes`：可选说明

---

### `relations`

这是替代原来 `connections` 的核心字段。

它表达的是：

> **模块之间存在什么架构关系**

而不是：

> **哪个端口连哪个端口**

#### `type` 建议枚举

* `power_flow`
* `data_path`
* `control_path`
* `sensing_path`
* `user_input_path`
* `protection_path`
* `clock_path`
* `storage_path`
* `generic_interface`

#### `intent`

一句短说明，描述这条关系的目的。
例如：

* `"supply regulated power to controller"`
* `"deliver keyboard scan signals to controller"`
* `"carry usb data toward host interface"`

#### `required`

布尔值。
表示这是系统必须存在的关系，还是可选关系。

---

### `open_issues`

第 1 步里它会很重要。
因为人类做结构设计时，本来也常常会保留一些“关系已知、接口未定”的问题。

例如：

* 控制器是否需要原生 USB
* 键盘矩阵是否用独立扫描芯片
* USB 数据路径是否还需 ESD / interface block

---

### `validation_targets`

这里最关键的一条是：

```json
"must_not_use_port_level_connections": true
```

这条是新版 schema 的边界锁。

---

# 3）新版 schema 的硬规则

## 必须规则

### 规则 1

`blocks.pb_class` 必须来自 registry，除非 `class_source = "generated_composite"`。

### 规则 2

`tier = "func"` 的 block 默认不能直接作为第 1 步输出，除非 `open_issues` 里说明为什么必须提前引入。

### 规则 3

`relations.from/to` 只能引用 block 的 `id`，不能写端口名。

错误示例：

```json
{ "from": "usb.pwr", "to": "reg.pwr_in" }
```

正确示例：

```json
{ "from": "usb", "to": "reg", "type": "power_flow" }
```

### 规则 4

每个 functional requirement 必须至少被一个 block 和一条 relation 覆盖。

### 规则 5

如果需求中出现 registry 里没有合适 top-level block 能表达的结构语义，应生成 `generated_composite`，而不是硬套 `func` block。

---

# 4）为什么这个 schema 更适合你现在的 registry

因为你当前 registry 的信息密度就是：

* 名称
* 简介
* tier
* 有些块有参数
* 有些块有 ports

它更适合回答：

* 系统里应该有哪些模块
* 这些模块之间应有什么高层关系

而不适合强行回答：

* 每条数据线具体从哪个 PB 端口到哪个 PB 端口

例如：

* `UsbDeviceConnector` 明确有 `pwr / gnd / usb`
* `VoltageRegulator` 明确有 `pwr_in / pwr_out / gnd`
* `IoController` 只有 `gnd / pwr`
* `Microcontroller` 连 `o` 都没有  

这正好说明：
**第 1 步 IR 不该绑定到端口级连接。**

---

# 5）USB 键盘案例，按新 schema 长什么样

```json
{
  "ir_version": "pb_arch_v1",
  "system": {
    "name": "UsbKeyboard",
    "goal": "USB keyboard with 3x2 key matrix",
    "design_stage": "architecture"
  },
  "requirements": {
    "functional": [
      "usb_connection",
      "power_conditioning",
      "programmable_control",
      "key_matrix_input"
    ],
    "constraints": [
      { "key": "matrix_rows", "value": 3 },
      { "key": "matrix_cols", "value": 2 }
    ]
  },
  "blocks": [
    {
      "id": "usb",
      "pb_class": "UsbDeviceConnector",
      "class_source": "registry",
      "tier": "sys",
      "role": "usb_connection",
      "params": {},
      "notes": ""
    },
    {
      "id": "reg",
      "pb_class": "VoltageRegulator",
      "class_source": "registry",
      "tier": "sys",
      "role": "power_conditioning",
      "params": {
        "output_voltage": 3.3
      },
      "notes": ""
    },
    {
      "id": "ctrl",
      "pb_class": "IoController",
      "class_source": "registry",
      "tier": "sys",
      "role": "programmable_control",
      "params": {},
      "notes": "controller type not yet refined"
    },
    {
      "id": "keys",
      "pb_class": "KeyMatrix",
      "class_source": "generated_composite",
      "tier": "sys",
      "role": "key_matrix_input",
      "params": {
        "rows": 3,
        "cols": 2
      },
      "notes": "generated because no suitable top-level matrix block exists in registry"
    }
  ],
  "relations": [
    {
      "from": "usb",
      "to": "reg",
      "type": "power_flow",
      "intent": "usb supplies raw input power to regulation stage",
      "required": true
    },
    {
      "from": "reg",
      "to": "ctrl",
      "type": "power_flow",
      "intent": "regulated power is supplied to controller",
      "required": true
    },
    {
      "from": "keys",
      "to": "ctrl",
      "type": "user_input_path",
      "intent": "key matrix provides scanable user input to controller",
      "required": true
    },
    {
      "from": "usb",
      "to": "ctrl",
      "type": "data_path",
      "intent": "usb communication path exists between connector side and controller side",
      "required": true
    }
  ],
  "open_issues": [
    {
      "type": "interface_unresolved",
      "target": "ctrl",
      "reason": "controller-side usb and gpio exposure are not yet represented at architecture stage"
    }
  ],
  "validation_targets": {
    "must_use_registry_classes": true,
    "must_respect_tier_policy": true,
    "must_cover_all_functional_requirements": true,
    "must_not_use_port_level_connections": true
  }
}
```

---

# 6）这个 schema 对 multi-agent 更友好的原因

以前 agent 会卡在：

* `mcu.usb` 到底合不合法
* `gpio` 在 registry 里有没有
* `Microcontroller` 为什么没 ports 却被连接了

现在 agent 改成评：

* 模块是否选对了
* 粒度是否合适
* 模块间关系是否覆盖需求
* 是否需要新建 composite block
* 有没有遗漏关键架构关系

这就更像人类在系统设计评审里做的事。

---

# 7）第 2 步再做什么

有了 `pb_arch_v1` 之后，第 2 步再单独做一个：

> **`pb_skeleton_v1`**

专门把：

* `blocks`
* `relations`

映射成：

* 更具体的 PB block 选择
* 端口级 connect 骨架
* unresolved ports / unresolved refinement

也就是：

**第 1 步：architecture IR**
**第 2 步：PB skeleton IR**
**第 3 步：细化 / refinement**

这个分层会稳很多。

---

## 最后一条定论

**新版 IR schema 应该把 `connections` 改成 `relations`，把第 1 步严格限定为“模块 + 架构关系”，不再要求 PB 端口级连接。**

如果你要，我下一步就直接把这个 schema 固化成一版**可供 LLM 输出的正式 JSON 模版**。
