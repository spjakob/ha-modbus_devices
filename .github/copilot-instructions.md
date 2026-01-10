## Purpose
This file tells AI coding agents how to be immediately productive in this repository.

## Big picture
- **Project type**: Home Assistant custom components for Modbus devices.
- **Key area**: device drivers live under `ha-modbus_devices/custom_components/modbus_devices/devices/` (example: `Eastron/SDM630.py`).

## What to inspect first
- Open: `ha-modbus_devices/custom_components/modbus_devices/devices/Eastron/SDM630.py` to understand the device-module layout and register-handling patterns.
- Look for: class definitions, mapping dictionaries (register → field), helper functions for read/write, and any constants used across modules.

## Common patterns and conventions in this repo
- Device modules are organized per vendor under `devices/<Vendor>/`.
- Expect each device file to contain one or more classes/functions that wrap Modbus register access — inspect how register addresses and scaling factors are represented.
- Naming: modules and classes use the device model name (e.g., `SDM630`) — follow the same naming when adding drivers.

## Integration and cross-component touchpoints
- Custom component root: `ha-modbus_devices/custom_components/modbus_devices/` — agents should scan here for platform registration, setup functions, and shared utilities.
- Shared utilities (if present) typically live adjacent to the integration package; prefer reuse over duplication.

## Developer workflows (quick, discoverable commands)
- To find device modules: `rg "custom_components/modbus_devices/devices" -n || true`.
- To search for common functions: `rg "async_setup" -n || true` and `rg "register" -n || true`.

## How an AI agent should operate here
- Always open the device module first to extract concrete register maps and example usages (no speculative changes before reading code).
- When adding or modifying a device, mirror existing file layout, naming, and register representation styles.
- Provide small, focused patches. Include unit-like smoke checks when possible (a minimal script that imports the module and exercises its register mapping is sufficient).

## Examples to reference
- Example device file: `ha-modbus_devices/custom_components/modbus_devices/devices/Eastron/SDM630.py` — use it as the canonical pattern for vendor/device structure and register handling.

## PR and commit guidance for agents
- Keep changes scoped to one device or one shared utility per PR.
- Include a short description referencing the device file(s) changed and why.

## When you need more context
- If important runtime behavior or CI commands are missing from the repo, ask the maintainer for: how to run Home Assistant dev mode for this integration, relevant dependencies, and any expected test commands.

If anything in this guidance is unclear or incomplete, tell me what additional files or workflows you want me to inspect and I will iterate.