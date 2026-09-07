---
name: forge-init
description: Initialize Forge Memory-First control memory in an existing project.
---

# Forge Init

Resolve the packaged resource
`forge-memory/assets/portable/scripts/forge-init` and invoke it through
`sys.executable`, passing the existing project directory as `PROJECT_ROOT`. In
a filesystem Agent Skills install, that resource is the sibling path
`../forge-memory/assets/portable/scripts/forge-init`; never resolve it from the
project being initialized:

`[sys.executable, BUNDLED_FORGE_INIT, PROJECT_ROOT]`

Report the command result. Do not pass `.forge` or rely on the current working
directory as the target.

The helper initializes and validates the control-memory layout, but a
placeholder Mission is not authority for substantive work. If initialization
reports the activation notice, the host maps the user-confirmed request into a
real Mission, publishes it through the safe replacement path, and validates it
before substantive implementation. The host performs this activation; the
helper does not infer or activate a Mission for the user.
