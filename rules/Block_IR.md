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