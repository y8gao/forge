---
name: forge-memory
description: Forge Memory-First control memory, mission state, checkpoints, compaction, archives, and deferred external recall.
---

# forge-memory

Forge memory keeps a small deterministic answer to "what is true and active
now?" in the project root's `.forge/` directory.

## Control memory

Control memory is canonical, human-reviewable Markdown:

- `.forge/INTENT.md` holds durable purpose, direction, active decisions,
  constraints, and non-goals.
- `.forge/MISSION.md` holds one active Mission. Outcome, Scope, and Success Criteria
  are its user-confirmed acceptance boundary. State, Latest Delivery, Next
  Action, Blockers, Last Check, and Resume are mutable continuity fields.

Only the host agent writes active control memory. Temporary agents and external
providers may suggest changes, but they never modify `INTENT.md` or
`MISSION.md`.

Routine checkpoints update MISSION only. Update INTENT only for a
user-confirmed durable project-level purpose, direction, decision, constraint,
or non-goal. Do not mirror Mission Outcome, State, Latest Delivery, Next Action,
Blockers, Last Check, or Resume into INTENT Direction.

For an authorized durable update, render the complete INTENT candidate outside
the active path, then invoke
`forge-intent PROJECT_ROOT --replace-from INTENT_FILE`. The helper prevalidates
all candidate bytes and atomically replaces `.forge/INTENT.md` through the
shared safe-write semantics. Never create, truncate, or patch active INTENT as
an intermediate draft.

Initialize missing active memory with `forge-init`. Validate it with
`forge-memory-validate`. Resolve every helper from the packaged resource
`forge-memory/assets/portable/scripts/` and invoke it through `sys.executable`;
in a filesystem Agent Skills install this is this skill's
`assets/portable/scripts/` directory.

## Concise active-memory schema

Keep `INTENT.md` within its parser boundary: INTENT has a maximum of 100 lines.
Keep `MISSION.md` similarly small: MISSION has a maximum of 60 lines.

The acceptance boundary in MISSION uses this executable summary:

```markdown
## Scope
- In: <included work>
- Out: <excluded work>
- Constraints: <delivery constraint>

## Success Criteria
- [ ] <nonempty criterion>
- [x] <nonempty completed criterion>
```

A valid Mission has at least one of each Scope line: `- In:`, `- Out:`, and
`- Constraints:`. Success Criteria contain one or more nonempty checklist items;
each item uses either `- [ ]` or `- [x]`.

## Mission state

MISSION state is one of `ready`, `working`, `blocked`, `paused`, or `done`.
These are exact wire-format tokens, not prose to translate or paraphrase;
`completed` is invalid. Copy an allowed token exactly whenever rendering or
checking Mission state. A `ready` Mission has `checkpointed_at: null`.
`working`, `blocked`, `paused`, and `done` require strict UTC
`YYYY-MM-DDTHH:MM:SSZ`.
Keep the active mission concise and current; it is not a task log, role ledger,
test matrix, or review history.

Outcome, Scope, and Success Criteria come from the user's words or explicit
confirmation. Changing one is a user-decision transition, not a routine status
update. Mutable continuity fields record only what is relevant to resuming that
Mission.

## Checkpoint triggers

Checkpoint only a real transition:

1. the user confirms or changes a decision, Outcome, Scope, or Success Criteria;
2. a visible delivery increment completes;
3. work pauses or transfers;
4. the active mission completes;
5. the active mission is replaced.

A checkpoint is mandatory when a real transition occurs. The five triggers
above are the complete trigger model; this does not create checkpoints for
individual reads, edits, tests, tool calls, or narration.

A pure question or read-only lookup is not a transition. Incidental work such
as a single-turn, reversible change must not be written into an unrelated
Mission. Do not checkpoint each tool call, edit, test, or internal step. Use
`forge-checkpoint` only after one of the transitions above. Resolve it as
`forge-memory/assets/portable/scripts/forge-checkpoint` (or this skill's
`assets/portable/scripts/forge-checkpoint` in a filesystem install).

forge-checkpoint mutates only continuity fields supported by that command:
State, checkpoint timestamp, Latest Delivery, Next Action, Blockers, Last Check,
and Resume.Do. It preserves Outcome, Scope, Success Criteria, and Resume.Read.
It cannot checkpoint to `ready`, and its generated timestamp must not be earlier
than the current non-null checkpointed_at; an equal second is valid.
For `blocked`, pass at least one current `--blocker`. Other states clear stale
blockers to `None.`. Resume.Do always follows the new Next Action.

For completion, invoke `forge-checkpoint PROJECT_ROOT --state done` with the
required delivery, next-action, and check evidence; do not hand-write a prose
state synonym. If Scope or Success Criteria also change in that turn, publish a
validated `working` Mission first, then complete it through forge-checkpoint.
After every active-memory write, run `forge-memory-validate` against the project.
Do not report a checkpoint or completion until validation passes.

The active `.forge/MISSION.md` is a publication destination, never a draft.
Use one of these two paths:

- Activation or replacement: render the complete candidate outside the active
  `.forge/MISSION.md` path as `ready` with `checkpointed_at: null`; validate all
  candidate bytes; publish them with `forge-compact --replace-from`; then run
  `forge-memory-validate`. Never create, patch, or repair the active Mission as
  an intermediate draft.
- Acceptance-boundary update: changing user-confirmed Scope or Success Criteria
  requires a direct validated host rewrite through the shared safe-write
  semantics; an Outcome change follows the same path. Form the complete
  candidate outside the active path, preserve the current State and
  checkpointed_at, validate the complete candidate, and publish it atomically;
  then use `forge-checkpoint` for the real state transition and current UTC
  timestamp. Do not extend forge-checkpoint beyond its narrow mutation contract.

For initial activation, map the confirmed request into Outcome, Scope, and
Success Criteria and follow the activation path above. This must publish and
validate a real `ready` Mission. Only then may substantive implementation begin.

## Compact and archive

Use `forge-compact` for archival transitions, resolving it as
`forge-memory/assets/portable/scripts/forge-compact` (or this skill's
`assets/portable/scripts/forge-compact` in a filesystem install). With
`--complete`, it archives exact MISSION bytes and leaves that `done` Mission
closed as active memory. It does not invent or activate a follow-up Mission.

For a confirmed replacement, first render the complete user-confirmed Outcome,
Scope, and Success Criteria into a parser-valid `ready` replacement MISSION
file with `checkpointed_at: null`, then pass that replacement MISSION file to
`forge-compact --replace-from`.
The command validates it and archives the old Mission before exact-byte
publication. Preserve published archives; if interrupted, follow the command's
recovery instruction rather than editing an archive by hand.

Archive is not loaded by default. `.forge/archive/` contains traceability and
legacy process material, not active authority. Read a specific archived file
only when the user asks for history or an unresolved question requires its
provenance.

Treat archive promotion as a new control-memory decision. Historical text may
inform a proposal, but moving it into active INTENT or MISSION requires separate
user confirmation; provenance or prior acceptance does not make it current.

## Control memory versus recall memory

Control memory states the current authoritative direction. Recall memory may
search historical sessions, documents, preferences, or learned experience.
Recall results must carry provenance and can only propose a control-memory
change for the host to decide.

External recall is deferred. The MVP has no embedded vector database, graph
memory, or external provider dependency, and recall can never become canonical
control memory.
