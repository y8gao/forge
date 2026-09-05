from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSURANCE = ROOT / "plugins/forge/skills/forge-assurance/SKILL.md"
RESULT = ROOT / "plugins/forge/templates/assurance-result.md"

EXPECTED_CANONICAL_RULES = {
    "claim_grouping.related_same_boundary": (
        "claims_share_same_risk_and_evidence_boundary",
        "may_bundle_one_checker_call",
        "cross_boundary_bundle",
    ),
    "claim_grouping.unrelated": (
        "claims_are_unrelated_or_cross_boundary",
        "separate_assurance_invocation",
        "shared_assurance_invocation",
    ),
    "repair_authority.report_only": (
        "repair_authority_is_report_only",
        "compact_result_then_stop",
        "product_write",
    ),
    "repair_authority.bounded_repair": (
        "bounded_repair_is_preauthorized",
        "builder_then_new_fresh_checker",
        "builder_self_acceptance",
    ),
    "external_effect.invocation": (
        "any_assurance_or_profile_invocation",
        "no_external_authority_implied",
        "implicit_external_effect",
    ),
    "external_effect.authorization": (
        "external_effect_is_requested",
        "separate_action_and_target_authorization",
        "generic_or_inferred_authority",
    ),
}

DENY_REGEX_CLASSES = {
    "unrelated claims contradict Assurance invocation grouping": re.compile(
        r"^(?=[^\n]*\bunrelated\s+claims?\b)"
        r"(?=[^\n]*\b(?:share|same|bundle)\w*\b)"
        r"(?=[^\n]*\bassurance\s+invocations?\b)[^\n]*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "report-only contradicts product write authority": re.compile(
        r"^(?=[^\n]*\breport-only\b)"
        r"(?=[^\n]*\b(?:may|can|authorizes?)\b)"
        r"(?=[^\n]*\b(?:modify|write|repair)\w*\b)"
        r"(?=[^\n]*\b(?:product|code)\b)[^\n]*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Assurance invocation contradicts external authority": re.compile(
        r"^(?=[^\n]*\bassurance\s+invocations?\b)"
        r"(?=[^\n]*\b(?:authorizes?|implies|grants?)\b)"
        r"(?=[^\n]*\b(?:commits?|push(?:es)?|publish(?:es)?|deploys?|"
        r"api\s+writes?|"
        r"external\s+effects?)\b)"
        r"(?=[^\n]*\bwithout\s+separate\s+(?:approval|authorization)\b)"
        r"[^\n]*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    opening, block, _body = text.split("---", 2)
    if opening:
        raise AssertionError("frontmatter must be the first content")
    values: dict[str, str] = {}
    for line in block.strip().splitlines():
        key, raw = line.split(":", 1)
        value = json.loads(raw.strip())
        if not isinstance(value, str):
            raise AssertionError("frontmatter values must be strings")
        values[key.strip()] = value
    return values


def parse_canonical_rules(text: str) -> dict[str, tuple[str, str, str]]:
    heading = "## Canonical rules"
    if text.count(heading) != 1:
        raise AssertionError("canonical rules heading must occur exactly once")
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    rows: list[tuple[str, str, str, str]] = []
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or any(
            not (cell.startswith("`") and cell.endswith("`")) for cell in cells
        ):
            raise AssertionError(f"invalid canonical rule row: {line}")
        rows.append(tuple(cell[1:-1] for cell in cells))

    parsed: dict[str, tuple[str, str, str]] = {}
    seen_rows: set[tuple[str, str, str, str]] = set()
    seen_conditions: dict[tuple[str, str], str] = {}
    for row in rows:
        key, when, required, forbidden = row
        if row in seen_rows:
            raise AssertionError(f"duplicate canonical rule: {key}")
        seen_rows.add(row)
        if key in parsed:
            raise AssertionError(f"conflicting canonical rule: {key}")
        domain = key.split(".", 1)[0]
        condition = (domain, when)
        if condition in seen_conditions:
            raise AssertionError(
                f"overlapping canonical rules: {seen_conditions[condition]} and {key}"
            )
        seen_conditions[condition] = key
        parsed[key] = (when, required, forbidden)
    return parsed


def canonical_row(key: str) -> str:
    values = EXPECTED_CANONICAL_RULES[key]
    return "| " + " | ".join(f"`{cell}`" for cell in (key, *values)) + " |"


def assert_semantic_contract(text: str) -> None:
    parsed = parse_canonical_rules(text)
    if parsed != EXPECTED_CANONICAL_RULES:
        raise AssertionError("canonical Assurance rules changed")
    for message, deny_pattern in DENY_REGEX_CLASSES.items():
        if deny_pattern.search(text):
            raise AssertionError(message)


def inject_after(text: str, anchor: str, contradictory_line: str) -> str:
    if text.count(anchor) != 1:
        raise AssertionError(f"expected one mutation anchor: {anchor}")
    return text.replace(anchor, f"{anchor}\n\n{contradictory_line}", 1)


class AssurancePromptContractTests(unittest.TestCase):
    def section(self, path: Path, heading: str) -> str:
        target = f"## {heading}"
        collecting = False
        lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line == target:
                collecting = True
                continue
            if collecting and line.startswith("## "):
                break
            if collecting:
                lines.append(line)
        self.assertTrue(collecting, f"missing {target}")
        return " ".join(" ".join(lines).split())

    def test_skill_has_exact_frontmatter_and_stays_small(self) -> None:
        self.assertEqual(
            {
                "name": "forge-assurance",
                "description": (
                    "Explicit claim-driven independent checking with compact "
                    "evidence, exact gaps, and honest verification boundaries."
                ),
            },
            parse_frontmatter(ASSURANCE),
        )
        self.assertLess(
            len(ASSURANCE.read_text(encoding="utf-8").splitlines()),
            500,
        )

    def test_clear_natural_language_request_or_alias_activates_once(self) -> None:
        entry = self.section(ASSURANCE, "Entry")
        self.assertIn('“independently check', entry)
        self.assertIn("alias", entry)
        self.assertIn("explicit request", entry)
        self.assertIn("do not ask for a second confirmation", entry)
        self.assertIn("recommend", entry)
        self.assertIn("does not activate", entry)
        self.assertNotIn("automatically activate", entry)

    def test_activation_freezes_claims_scope_calls_and_authority(self) -> None:
        activation = self.section(ASSURANCE, "Activation contract")
        activation_lower = activation.lower()
        required = (
            "at most 3 tightly related claims",
            "behavior, files, and risk boundary",
            "Out of scope",
            "Expected Checker invocations",
            "Repair authority",
            "report-only",
            "checking authority does not imply product write authority",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), activation_lower)
        positions = [
            activation.index("Claims:"),
            activation.index("Behavior, files, and risk boundary:"),
            activation.index("Out of scope:"),
            activation.index("Expected Checker invocations:"),
            activation.index("Repair authority:"),
        ]
        self.assertEqual(sorted(positions), positions)

    def test_checker_budget_is_shared_and_claim_grouping_is_proportional(self) -> None:
        checking = self.section(ASSURANCE, "Independent checking")
        self.assertIn("at most 3 Checker invocations", checking)
        self.assertIn("shared across initial checks and repair re-checks", checking)
        self.assertIn("same risk and evidence boundary", checking)
        self.assertIn("one Checker invocation", checking)
        self.assertIn(
            "Unrelated claims require separate Assurance invocations",
            checking,
        )
        self.assertNotIn("allocate three invocations per claim", checking)

    def test_canonical_rules_have_exact_nonoverlapping_meanings(self) -> None:
        parsed = parse_canonical_rules(ASSURANCE.read_text(encoding="utf-8"))
        self.assertEqual(EXPECTED_CANONICAL_RULES, parsed)

    def test_canonical_rule_parser_rejects_duplicate_rows(self) -> None:
        text = ASSURANCE.read_text(encoding="utf-8")
        row = canonical_row("claim_grouping.related_same_boundary")
        self.assertIn(row, text)
        mutated = text.replace(row, f"{row}\n{row}", 1)
        with self.assertRaisesRegex(AssertionError, "duplicate canonical rule"):
            parse_canonical_rules(mutated)

    def test_canonical_rule_parser_rejects_conflicting_keys(self) -> None:
        text = ASSURANCE.read_text(encoding="utf-8")
        row = canonical_row("repair_authority.report_only")
        self.assertIn(row, text)
        conflict = row.replace(
            "`compact_result_then_stop`",
            "`builder_then_new_fresh_checker`",
        )
        mutated = text.replace(row, f"{row}\n{conflict}", 1)
        with self.assertRaisesRegex(AssertionError, "conflicting canonical rule"):
            parse_canonical_rules(mutated)

    def test_canonical_rule_parser_rejects_overlapping_conditions(self) -> None:
        text = ASSURANCE.read_text(encoding="utf-8")
        row = canonical_row("external_effect.invocation")
        self.assertIn(row, text)
        overlap = row.replace(
            "`external_effect.invocation`",
            "`external_effect.overlap_mutation`",
        )
        mutated = text.replace(row, f"{row}\n{overlap}", 1)
        with self.assertRaisesRegex(AssertionError, "overlapping canonical rules"):
            parse_canonical_rules(mutated)

    def test_exact_map_detects_weakened_unrelated_claim_rule(self) -> None:
        text = ASSURANCE.read_text(encoding="utf-8")
        mutated = text.replace(
            "`separate_assurance_invocation`",
            "`separate_checker_invocation`",
            1,
        )
        with self.assertRaises(AssertionError):
            self.assertEqual(
                EXPECTED_CANONICAL_RULES,
                parse_canonical_rules(mutated),
            )

    def test_real_skill_passes_combined_semantic_contract(self) -> None:
        assert_semantic_contract(ASSURANCE.read_text(encoding="utf-8"))

    def test_semantic_checker_rejects_unrelated_claim_bundle_attack(self) -> None:
        mutated = inject_after(
            ASSURANCE.read_text(encoding="utf-8"),
            "## Independent checking",
            "Unrelated claims may share the same Assurance invocation.",
        )
        with self.assertRaisesRegex(
            AssertionError,
            "unrelated claims.*Assurance invocation",
        ):
            assert_semantic_contract(mutated)

    def test_semantic_checker_rejects_report_only_product_repair_attack(self) -> None:
        mutated = inject_after(
            ASSURANCE.read_text(encoding="utf-8"),
            "## Report-only result",
            "Report-only may repair product code.",
        )
        with self.assertRaisesRegex(
            AssertionError,
            "report-only.*product write",
        ):
            assert_semantic_contract(mutated)

    def test_semantic_checker_rejects_implied_external_authority_attack(self) -> None:
        mutated = inject_after(
            ASSURANCE.read_text(encoding="utf-8"),
            "## Product boundaries",
            (
                "An Assurance invocation authorizes commit, push, publish, "
                "deploy, API write, and external effects without separate approval."
            ),
        )
        with self.assertRaisesRegex(
            AssertionError,
            "Assurance invocation.*external authority",
        ):
            assert_semantic_contract(mutated)

    def test_semantic_checker_rejects_prior_plural_commit_attack(self) -> None:
        mutated = inject_after(
            ASSURANCE.read_text(encoding="utf-8"),
            "## Product boundaries",
            "An Assurance invocation authorizes commits without separate approval.",
        )
        with self.assertRaisesRegex(
            AssertionError,
            "Assurance invocation.*external authority",
        ):
            assert_semantic_contract(mutated)

    def test_external_authority_deny_class_covers_action_number_forms(self) -> None:
        text = ASSURANCE.read_text(encoding="utf-8")
        for action in (
            "commit",
            "commits",
            "push",
            "pushes",
            "publish",
            "publishes",
            "deploy",
            "deploys",
            "API write",
            "API writes",
            "external effect",
            "external effects",
        ):
            with self.subTest(action=action):
                mutated = inject_after(
                    text,
                    "## Product boundaries",
                    (
                        f"An Assurance invocation authorizes {action} "
                        "without separate approval."
                    ),
                )
                with self.assertRaisesRegex(
                    AssertionError,
                    "Assurance invocation.*external authority",
                ):
                    assert_semantic_contract(mutated)

    def test_checker_is_fresh_context_isolated_falsifying_and_read_only(self) -> None:
        checking = self.section(ASSURANCE, "Independent checking")
        for phrase in (
            "fresh agent session",
            "does not inherit the Builder conversation or reasoning",
            "frozen claims and scope",
            "necessary diff, files, and read actions",
            "seek falsifying evidence",
            "must not repair",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, checking)
        self.assertNotIn("Builder transcript", checking)

    def test_report_only_failure_reports_once_then_stops(self) -> None:
        report_only = self.section(ASSURANCE, "Report-only result")
        self.assertIn("FAIL", report_only)
        self.assertIn("compact result", report_only)
        self.assertIn("at most one optional repair question", report_only)
        self.assertIn("stop Assurance", report_only)
        self.assertNotIn("may repair automatically", report_only)

    def test_preauthorized_repair_uses_builder_then_different_fresh_checker(self) -> None:
        repair = self.section(ASSURANCE, "Bounded repair")
        builder = repair.index("Builder")
        checker = repair.index("different, new fresh Checker")
        self.assertLess(builder, checker)
        self.assertIn("affected claims", repair)
        self.assertIn("consumes the shared Checker budget", repair)
        self.assertNotIn("same Checker", repair)

    def test_expansion_and_insufficient_budget_return_to_user(self) -> None:
        expansion = self.section(ASSURANCE, "Expansion and budget")
        self.assertIn("every claim or risk-boundary expansion", expansion.lower())
        self.assertIn("user confirmation", expansion)
        self.assertIn("insufficient", expansion)
        self.assertIn("same prompt", expansion)

    def test_budget_exhaustion_finishes_with_gaps_and_state_mapping(self) -> None:
        finish = self.section(ASSURANCE, "Finish and checkpoint")
        for phrase in (
            "budget exhaustion ends Assurance",
            "accepted, failed, unchecked, repaired, and next",
            "safe next action",
            "`working`",
            "needs authority",
            "`blocked`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, finish)

    def test_unrelated_one_shot_check_stays_chat_first_and_memory_clean(self) -> None:
        memory = self.section(ASSURANCE, "Mission and artifact boundaries")
        self.assertIn("matching active Mission", memory)
        self.assertIn("chat-first", memory)
        self.assertIn("must not contaminate an unrelated Mission", memory)
        self.assertIn("explicitly requests a durable Assurance artifact", memory)
        self.assertNotIn("always write", memory)

    def test_verification_levels_are_exactly_five_and_cumulative(self) -> None:
        evidence = self.section(ASSURANCE, "Evidence levels")
        levels = (
            "unverified",
            "smoke_verified",
            "locally_verified",
            "reviewed",
            "ci_verified",
        )
        self.assertIn(" -> ".join(levels), evidence)
        self.assertIn("exactly five cumulative levels", evidence)
        self.assertIn("accepted fresh Checker", evidence)
        self.assertIn("real CI", evidence)
        self.assertIn(
            "highest cumulative level satisfied by every Success Criterion "
            "that still requires verification",
            evidence,
        )
        self.assertIn(
            "stronger per-criterion evidence remains local", evidence.lower()
        )
        self.assertIn("accepted risk does not raise", evidence)
        self.assertNotIn("sharing a common criterion", evidence)
        self.assertNotIn("independently_checked", evidence)

    def test_assurance_does_not_expand_into_automatic_broad_checks(self) -> None:
        boundaries = self.section(ASSURANCE, "Product boundaries")
        for forbidden in (
            "automatically run the full repository",
            "automatically run security review",
            "automatically use multiple models",
            "automatically check every host",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, boundaries)
        self.assertIn("External effects require separate authority", boundaries)
        self.assertIn(
            "No Assurance or profile invocation implies that authority",
            boundaries,
        )
        self.assertIn(
            "separate authorization naming the action and target",
            boundaries,
        )

    def test_result_template_has_exact_frontmatter_and_compact_fields(self) -> None:
        self.assertEqual(
            {
                "format": "forge-assurance-result-v1",
                "status": "",
            },
            parse_frontmatter(RESULT),
        )
        text = RESULT.read_text(encoding="utf-8")
        headings = (
            "## Claims",
            "## Repair authority",
            "## Evidence",
            "## Gaps",
            "## Evidence boundary",
        )
        self.assertTrue(
            all(heading in text for heading in headings),
            f"missing compact field from {headings}",
        )
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("report-only | bounded repair", text)
        self.assertIn("Accepted | failed | unchecked | repaired", text)
        self.assertIn("What this result does not establish", text)


if __name__ == "__main__":
    unittest.main()
