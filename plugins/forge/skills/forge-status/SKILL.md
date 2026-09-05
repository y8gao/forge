---
name: forge-status
description: Show the current Forge Memory-First mission from active project memory.
---

# Forge Status

Resolve the bundled `plugins/forge/scripts/forge-status` script and invoke it
through `sys.executable`, passing the project directory as `PROJECT_ROOT`:

`[sys.executable, BUNDLED_FORGE_STATUS, PROJECT_ROOT]`

Return the script output unchanged. Do not pass `.forge` or infer status from
other project artifacts.
