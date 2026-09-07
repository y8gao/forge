---
name: forge-status
description: Show the current Forge Memory-First mission from active project memory.
---

# Forge Status

Resolve the packaged resource
`forge-memory/assets/portable/scripts/forge-status` and invoke it through
`sys.executable`, passing the project directory as `PROJECT_ROOT`. In a
filesystem Agent Skills install, that resource is the sibling path
`../forge-memory/assets/portable/scripts/forge-status`; never resolve it from
the target project:

`[sys.executable, BUNDLED_FORGE_STATUS, PROJECT_ROOT]`

Return the script output unchanged. Do not pass `.forge` or infer status from
other project artifacts.
