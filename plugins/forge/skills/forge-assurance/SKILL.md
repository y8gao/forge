---
name: "forge-assurance"
description: "Explicit claim-driven independent checking with compact evidence, exact gaps, and honest verification boundaries."
---

# Forge Assurance

Assurance is a prompt-layer checking mode. It does not create a fixed role
pipeline, policy runtime, scheduler, or automatic gate.

## Entry

A clear natural-language request such as “independently check these claims” or
an Assurance alias is an explicit request. Start Assurance and do not ask for a
second confirmation when the request and scope are clear.

Forge may recommend Assurance for a risky surface, but a recommendation does
not activate Assurance. Risk alone never activates it.

## Activation contract

Before launching a Checker, freeze this concise contract:

1. Claims: at most 3 tightly related claims.
2. Behavior, files, and risk boundary: what each claim covers.
3. Out of scope: what will not be checked.
4. Expected Checker invocations: the planned claim grouping and call count.
5. Repair authority: `report-only` by default, or a user-authorized bounded
   repair scope.

Checking authority does not imply product write authority. A request to check
does not imply repair authority, and repair authority does not imply permission
for external effects.

## Canonical rules

This compact table is normative. The prose around it explains the same rules
for people; it must not weaken or contradict these outcomes.

| Rule | When | Required | Forbidden |
| --- | --- | --- | --- |
| `claim_grouping.related_same_boundary` | `claims_share_same_risk_and_evidence_boundary` | `may_bundle_one_checker_call` | `cross_boundary_bundle` |
| `claim_grouping.unrelated` | `claims_are_unrelated_or_cross_boundary` | `separate_assurance_invocation` | `shared_assurance_invocation` |
| `repair_authority.report_only` | `repair_authority_is_report_only` | `compact_result_then_stop` | `product_write` |
| `repair_authority.bounded_repair` | `bounded_repair_is_preauthorized` | `builder_then_new_fresh_checker` | `builder_self_acceptance` |
| `external_effect.invocation` | `any_assurance_or_profile_invocation` | `no_external_authority_implied` | `implicit_external_effect` |
| `external_effect.authorization` | `external_effect_is_requested` | `separate_action_and_target_authorization` | `generic_or_inferred_authority` |

## Independent checking

Use at most 3 Checker invocations, shared across initial checks and repair
re-checks. Tightly related claims may share one Checker invocation only when
they have the same risk and evidence boundary and one coherent attack can
falsify them. Unrelated claims require separate Assurance invocations, not
merely separate Checker calls within one Assurance. Do not budget three
invocations per claim.

Every independent Checker runs in a fresh agent session that does not inherit
the Builder conversation or reasoning. Give it only the frozen claims and
scope, the necessary diff, files, and read actions, and a bounded return
contract. It must seek falsifying evidence, remain read-only on the product,
and must not repair.

The host accepts or rejects each returned result against the frozen claim and
preserves exact commands, outcomes, skips, failures, and unchecked boundaries.

## Report-only result

For a report-only FAIL, return one compact result with the evidence and exact
gaps. Ask at most one optional repair question, then stop Assurance. Do not
repair automatically or continue checking an expanded scope.

## Bounded repair

When bounded repair was preauthorized, record the failed check, send only the
authorized failure scope to a Builder, then use a different, new fresh Checker
to re-check the affected claims. The re-check consumes the shared Checker
budget. The Builder cannot accept its own repair, and the original Checker
cannot silently become the repairer.

## Expansion and budget

Every claim or risk-boundary expansion requires user confirmation before more
work. If the remaining Checker budget is insufficient, the host may request
the expansion and additional budget in the same prompt. Silence never grants
either.

## Finish and checkpoint

Cancellation, an unrepaired failure, or budget exhaustion ends Assurance.
Report accepted, failed, unchecked, repaired, and next outcomes, including
whether repair was attempted and every exact gap.

Checkpoint only when the Assurance result belongs to the matching active
Mission. If there is a safe next action, leave that Mission `working`. If the
next action needs authority or no safe action remains, mark it `blocked`.

## Mission and artifact boundaries

Only a result for the matching active Mission may update its checkpoint. An
unrelated one-shot check stays chat-first unless the user asks for a new
Mission; it must not contaminate an unrelated Mission.

Use the fields in `plugins/forge/templates/assurance-result.md` for the compact
result. Write a durable Assurance artifact only when the user explicitly
requests a durable Assurance artifact.

## Evidence levels

Forge has exactly five cumulative levels:
`unverified -> smoke_verified -> locally_verified -> reviewed -> ci_verified`.
There is no sixth Assurance-specific level. `reviewed` requires an accepted
fresh Checker result for the claim. `ci_verified` requires that reviewed
evidence plus real CI evidence for the same criterion.

The Mission-level verification level is the highest cumulative level satisfied
by every Success Criterion that still requires verification. Stronger
per-criterion evidence remains local. An accepted risk does not raise the
verification level.

## Product boundaries

Assurance does not automatically run the full repository, automatically run
security review, automatically use multiple models, or automatically check
every host. Select only checks required to falsify the frozen claims.

External effects require separate authority, including commit, push, deploy,
publish, API writes, or messages. No Assurance or profile invocation implies
that authority; each external effect requires separate authorization naming
the action and target. Assurance is claim-driven, not a fixed role pipeline or
automatic gate.
