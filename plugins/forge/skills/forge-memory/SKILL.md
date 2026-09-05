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

Initialize missing active memory with `forge-init`. Validate it with
`forge-memory-validate`.

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
checking Mission state.
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

A pure question or read-only lookup is not a transition. Incidental work such
as a single-turn, reversible change must not be written into an unrelated
Mission. Do not checkpoint each tool call, edit, test, or internal step. Use
`forge-checkpoint` only after one of the transitions above.

forge-checkpoint mutates only continuity fields supported by that command:
State, checkpoint timestamp, Latest Delivery, Next Action, Blockers, Last Check,
and Resume.Do. It preserves Outcome, Scope, Success Criteria, and Resume.Read.
For `blocked`, pass at least one current `--blocker`. Other states clear stale
blockers to `None.`. Resume.Do always follows the new Next Action.

For completion, invoke `forge-checkpoint PROJECT_ROOT --state done` with the
required delivery, next-action, and check evidence; do not hand-write a prose
state synonym. If Scope or Success Criteria also change in that turn, publish a
validated `working` Mission first, then complete it through forge-checkpoint.
After every active-memory write, run `forge-memory-validate` against the project.
Do not report a checkpoint or completion until validation passes.

Changing user-confirmed Scope or Success Criteria requires a direct validated
host rewrite through the shared safe-write semantics. The host validates the
complete Mission before publishing it; do not invent a separate script or
extend forge-checkpoint to bypass its narrow mutation contract.

## Compact and archive

Use `forge-compact` for archival transitions. With `--complete`, it archives
exact MISSION bytes and leaves that `done` Mission closed as active memory. It
does not invent or activate a follow-up Mission.

For a confirmed replacement, first render the complete user-confirmed Outcome,
Scope, and Success Criteria into a parser-valid `ready` replacement MISSION
file, then pass that replacement MISSION file to `forge-compact --replace-from`.
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
