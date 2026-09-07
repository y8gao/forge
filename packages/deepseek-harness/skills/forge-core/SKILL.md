---
name: forge-core
description: Forge Memory-First default behavior for orientation, ordinary execution, checkpoints, proportional checks, and explicit Loop or Assurance entry.
---

# forge-core

Forge Core is the lightweight default for a host coding agent. Its purpose is
continuity and useful delivery, not workflow governance.

## Start from the user's request

Natural-language requests are the primary entry point. Aliases are optional.
The user does not need to understand profiles, checkpoints, or invocation syntax.
Core interprets the request, preserves the user's authority, and chooses the
smallest path that can produce a useful, checked result.

The ordinary path is:

```text
Orient -> understand the request -> choose the first minimum sufficient path
       -> act directly or select one useful profile
       -> targeted check -> checkpoint only on a real transition
```

There is no automatic delegation, review artifact, fixed role chain, preflight,
gate ladder, Loop, or Assurance. A temporary profile is useful only when its
focused capability improves the current task; otherwise the host works directly.

## Orient and resume safely

Read only `.forge/INTENT.md` and `.forge/MISSION.md` as active control memory.
If either is missing, initialize it and ask only for project facts that cannot
be inferred safely. Recover Outcome, Scope, Success Criteria, state, Latest
Delivery, Next Action, Blockers, Last Check, and Resume.

Do not load archives, reviews, databases, or process history by default. Read
specific history only when the user asks or an unresolved question requires
its provenance.

On a fresh resume, state controls what is safe:

- `ready` or `working` with a safe Next Action may continue.
- `paused` requires the user to resume before work continues.
- `blocked` requires resolving or revising the blocker first.
- `done` stays closed unless the user confirms a new Mission.

## Keep unrelated work separate

A pure question or read-only lookup does not replace or checkpoint the active
Mission. Answer or inspect, report the evidence boundary, and leave continuity
state unchanged.

A single-turn, reversible incidental change may be completed under the user's
request without replacing an unrelated Mission. The host reports the change and
checks and does not checkpoint it into an unrelated Mission. If the request
materially changes the active Outcome, Scope, Success Criteria, or continuation
state, compare it with active INTENT and MISSION first. If that comparison finds
a conflict or material impact, expose the conflict and ask the user to adopt,
adapt, or discard the change before updating memory. Do not add another
confirmation turn when the request is compatible and its boundary is complete.

## Understand before choosing a solution

Follow the user's requested scope. Clarify only material ambiguity: uncertainty
that changes scope, destructive effects, public behavior, cost, or accepted
risk. For a small, reversible assumption, choose a reasonable value and report
it instead of blocking useful work.

For implementation, understand the existing control flow and data flow first,
then climb only as far as needed:

1. Confirm each criterion is necessary.
2. Reuse the existing repository and its current patterns.
3. Prefer the standard library or native capability.
4. Use an already-installed dependency when it is the minimum safe fit.
5. Build the minimum safe custom solution only when the earlier steps fail.

Stop at the first solution that satisfies the acceptance boundary safely. Do
not broaden scope merely because a more elaborate implementation is possible.

## Offer Loop once for complex work

When work has several coupled slices, meaningful uncertainty, or a bounded
iteration would materially help, Ask once whether the user wants Loop. Present
this one concise card:

```text
Outcome: <the requested result>
Done when: <observable acceptance criteria>
Boundaries: <scope, risk, and authority limits>
Budget: <iteration and agent limits>
```

Do not enter Loop automatically. Enter only after the user accepts the complete
card through natural language or an optional alias. Declining Loop is not
cancelling the original task. Continue under the original authority with at
most one minimum safe Core delivery, a plan-only response, or stop when no safe
delivery is available; report what remains.

Assurance is also explicit. Core may recommend it for a material risk, but a
recommendation is not activation.

## Check and report proportionally

Use the minimum sufficient falsifying evidence for the changed behavior and
risk: start with a targeted check and broaden only when justified. Report exact
commands, outcomes, assumptions, and anything not checked.

Verification levels are ordered and cumulative:
`unverified -> smoke_verified -> locally_verified -> reviewed -> ci_verified`.
Local checks reach at most `locally_verified`; `reviewed` requires actual
independent checking, and `ci_verified` requires evidence from real CI.

Only the host writes active control memory. Checkpoint a user-confirmed outcome
or boundary change, visible delivery, pause, completion, or Mission replacement.
Do not checkpoint tool calls, internal steps, pure lookups, or unrelated
incidental work.
After every active-control-memory write, run `forge-memory-validate` against the
project. Do not report Mission completion until post-write validation passes.

## Preserve external-effect authority

No mode, profile, or workflow choice grants permission for external side effects.
Commit, push, publish, deploy, destructive operations, paid actions, and other
external effects still require the user's explicit authority when applicable.

## Correcting deviations

When output diverges from the request, classify the cause before repairing it:
expectation drift, design deviation, implementation defect, or verification
gap. Do not hide a scope conflict with a local workaround.
