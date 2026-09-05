---
name: forge-init
description: Initialize Forge Memory-First control memory in an existing project.
---

# Forge Init

Resolve the bundled `plugins/forge/scripts/forge-init` script and invoke it
through `sys.executable`, passing the existing project directory as
`PROJECT_ROOT`:

`[sys.executable, BUNDLED_FORGE_INIT, PROJECT_ROOT]`

Report the command result. Do not pass `.forge` or rely on the current working
directory as the target.
