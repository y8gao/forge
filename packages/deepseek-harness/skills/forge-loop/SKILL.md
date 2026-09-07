---
name: "forge-loop"
description: "Explicit prompt-only bounded delivery loop with visible deltas, falsifying checks, and host-owned checkpoints."
---

# Forge Loop

Loop is explicit, prompt-only bounded continuation run by the host. Complexity
never activates Loop automatically, and Loop does not automatically activate
Assurance.

## Confirm entry

Only Core proactively recommends Loop, presents the card, and asks whether to
enter.

For a Core-recommended entry, Core already showed the complete card and the user
approved it. Loop must validate and record the already accepted card, then
start; it must not show or echo it again.

A `forge-loop` alias or a clear natural-language request for bounded
continuation is a direct entry request. Use this card for direct entry:

```text
Outcome: <specific result>
Done when: <measurable completion criteria>
Boundaries: <Scope In, Scope Out, writes, destructive limits, authority>
Budget: <iterations and temporary-agent invocations>
```

Validate that the outcome is Specific, Measurable, Achievable, Relevant, and
Time-bounded. Confirm Scope In, Scope Out, allowed write scope, forbidden or
destructive operations, and completion conditions. Ask only focused questions
for missing facts that change execution, acceptance, risk, or external
authority. The host must not guess or infer the Loop outcome, scope, or
acceptance criteria.

If the direct entry request already fully specifies and authorizes the outcome,
scope and criteria, boundaries, and either a budget or the defaults, the host
constructs and shows exactly one card as acknowledgement, then starts without
asking for redundant approval. The complete request supplies that approval.

If the entry request is incomplete, ask only for missing material facts. Do not
repeat facts the user already supplied. Then show the completed card exactly
once and start only when the user explicitly replies to approve it.

If the user declines Loop, that is not cancelling the original task. Continue
under the authority already granted with at most one minimum safe Core delivery,
a plan-only response when requested, or an explicit stop. Report remaining
work.

## Bound one invocation

The defaults are 3 delivery iterations and 5 temporary-agent invocations. The
user may override either at activation with positive integers. Apply the stated
defaults or overrides exactly, with no adaptive budget engine or arbitrary
hidden caps. Each parallel agent counts separately; an agent launch counts even
when it fails or is cancelled. Starting a delivery cycle consumes one
iteration, and a cycle with no visible delta still consumes that iteration.

Counters remain only in the current conversation. Cross-session continuation
starts a new invocation with a new budget after revalidating the persisted
outcome, scope, and success criteria. Do not persist counters in active memory
or create a scheduler, daemon, ledger, policy engine, or runtime state machine.

## Deliver one inspectable result

Each delivery cycle is:

```text
Orient -> choose one user-inspectable visible delta -> Act or Delegate
       -> targeted falsifying check -> lightweight economy check
       -> Host accepts -> one checkpoint -> continue or stop
```

The host performs ordinary actions directly first. It may use Scout or Builder
only when useful for a bounded discovery or implementation slice. The visible
delta must advance the Mission: working behavior, an accepted decision, a
reproducible diagnostic conclusion, a requested artifact, or a removed
blocker. These do not count as delivery: reading files, launching agents,
internal plans, and progress narration. Never manufacture an artifact to keep
Loop running.

Use targeted tests, lint, builds, inspection, or other falsifying evidence
appropriate to the delta. Before acceptance, confirm criteria and risk coverage,
then perform a lightweight economy check: were calls, files, dependencies,
abstractions, wrappers, and configuration necessary, and could an existing
repository, standard-library, native, or installed capability meet every
criterion more simply? This is part of host acceptance, not another gate or
artifact. Ordinary Loop verification does not automatically call Checker.

Only the host accepts results and writes active memory. One cycle produces at
most one accepted visible delta and one checkpoint.

## Delegate without collisions

Parallel delegation is allowed only when tasks are independent and do not share
write state. Temporary agents cannot delegate to other agents. Builders with
overlapping write scopes cannot run in parallel. The host waits for relevant
returns before acceptance and integrates them itself.

If overlap is discovered after launch, stop accepting both returns. The host
cancels them when safe or waits for completion, inspects the actual diff, and
keeps the results unaccepted. Recover by lossless serialization when possible.
Otherwise set the Mission to `blocked` and ask the user to adopt, adapt, or
discard; the host does not automatically revert user work.

## Canonical stop mapping

Each condition key appears once:

```text
outcome-complete => done
budget-exhausted => working
required-current-plan-decision => blocked
unsafe-path => blocked
no-safe-next-action => blocked
same-root-cause-twice => blocked
explicit-user-pause => paused
material-redirect-comparison => paused
no-visible-delta-safe-recovery => working
no-visible-delta-no-safe-recovery => blocked
```

These are terminal states for one Loop invocation, not a runtime transition
engine. `ready` remains the pre-execution Mission state and is not a Loop stop.

## Stop once and preserve evidence

Every stop reports the reason, accepted deliveries, checks actually run,
remaining work, and evidence boundary. Write an accepted visible delta and stop
in one checkpoint; never split one transition into two active-memory writes. A
no-delta stop records no fabricated Latest Delivery.

After the first failed cycle, persist the classified root cause, key evidence,
and attempted recovery in existing Last Check or Blockers. This compact fact,
not a counter or ledger, lets a later invocation identify the same root cause
twice.

## Canonical redirect matrix

Each trigger appears in exactly one action group:

```text
pause => material-outcome-change, material-scope-change, material-success-criteria-change, material-authority-change, in-flight-work-invalidated
continue => pure-question, status-request, continue-request, non-authority-clarification
```

The pause group means the instruction materially changes Outcome, Scope,
Success Criteria, or authority, or invalidates in-flight work. The continue
group leaves authority and in-flight validity unchanged.

## Redirect safely

Apply the canonical redirect matrix before changing Mission state. Only a
`pause` trigger suspends old execution authority. A `continue` trigger proceeds
under current authority without a pause checkpoint.

On a material redirect, the old invocation stops accepting results and
checkpointing. The Mission remains `paused`. Classify the change as correction,
scope amendment, conflict, or mission replacement, and explain its impact.
The host must cancel in-flight work when safe or wait for completion. If an
in-place Builder cannot be cancelled, the host waits for an in-place Builder to
return. Inspect the actual working-tree change and mark affected results stale
and unaccepted.

Then write exactly one redirect pause checkpoint recording accepted delivery
and stale or unaccepted status before the host may request user disposition.
The host may present the disposition and a complete new Loop card in one prompt;
one reply may authorize both clearly separated decisions.

After the user confirms the target Mission and Scope, the host re-inspects the
stale result and accepts it only if it fits that target. Discarding in-place
changes requires explicit authorization and must not silently revert unrelated
user work. Subsequent changes belong only to the new authority.

## Preserve external authority

No Loop invocation implies permission for an external side effect. Commit,
push, publish, deploy, messaging, cloud or API writes, deletion, and other
external writes each require authorization for the specific action and target,
whether granted in the original request, the Loop card, or immediately before
the action. A profile cannot broaden that authority.
