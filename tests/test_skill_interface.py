from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/forge/skills"
PUBLIC_SKILLS = {
    "forge-init",
    "forge-status",
    "forge-loop",
    "forge-assurance",
}
INTERNAL_SKILLS = {
    "forge-core",
    "forge-memory",
    "forge-scout",
    "forge-builder",
    "forge-checker",
}
EXPECTED_DESCRIPTIONS = {
    "forge-init": (
        "Use when a project does not yet contain valid Forge INTENT.md and "
        "MISSION.md control memory."
    ),
    "forge-status": (
        "Use when the user asks for the current Forge Mission, progress, "
        "blockers, next action, or verification boundary."
    ),
    "forge-loop": (
        "Use when the user explicitly requests bounded iterative continuation "
        "with a defined outcome, scope, and iteration budget."
    ),
    "forge-assurance": (
        "Use when the user explicitly requests an independent check of concrete "
        "claims or authorizes bounded repair after findings."
    ),
    "forge-core": (
        "Use when entering or resuming ordinary work in a Forge-managed project "
        "and no explicit Loop or Assurance request is active."
    ),
    "forge-memory": (
        "Use when existing Forge control memory must be updated, validated, "
        "checkpointed, paused, resumed, archived, or replaced."
    ),
    "forge-scout": (
        "Use when the host needs focused read-only evidence or provenance "
        "before a decision or implementation change."
    ),
    "forge-builder": (
        "Use when the host has confirmed write authority and a declared "
        "implementation scope for a focused change."
    ),
    "forge-checker": (
        "Use when an explicit Assurance or independent-check request requires "
        "fresh read-only falsification of concrete claims."
    ),
}


def frontmatter(name: str) -> dict[str, str]:
    lines = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing frontmatter: {name}")
    closing = lines.index("---", 1)
    result: dict[str, str] = {}
    for line in lines[1:closing]:
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


class SkillInterfaceTests(unittest.TestCase):
    def test_descriptions_are_exact_trigger_only_discovery_conditions(
        self,
    ) -> None:
        self.assertEqual(PUBLIC_SKILLS | INTERNAL_SKILLS, set(EXPECTED_DESCRIPTIONS))
        for name, expected in EXPECTED_DESCRIPTIONS.items():
            with self.subTest(skill=name):
                description = frontmatter(name).get("description")
                self.assertEqual(expected, description)
                self.assertTrue(description.startswith("Use when"))
                self.assertLess(len(description), 500)

    def test_exact_description_copy_has_one_test_owner(self) -> None:
        for path in (ROOT / "tests").glob("test_*.py"):
            if path == Path(__file__):
                continue
            text = path.read_text(encoding="utf-8")
            for name, description in EXPECTED_DESCRIPTIONS.items():
                with self.subTest(path=path.name, skill=name):
                    self.assertNotIn(description, text)

    def test_public_interface_is_exactly_four_user_invocable_skills(self) -> None:
        actual = {
            path.name
            for path in SKILLS.iterdir()
            if frontmatter(path.name).get("user-invocable") == "true"
        }
        self.assertEqual(PUBLIC_SKILLS, actual)

    def test_internal_skills_are_model_available_but_not_user_invocable(
        self,
    ) -> None:
        for name in INTERNAL_SKILLS:
            with self.subTest(skill=name):
                metadata = frontmatter(name)
                self.assertEqual("false", metadata.get("user-invocable"))
                self.assertNotEqual(
                    "true",
                    metadata.get("disable-model-invocation"),
                )

    def test_loop_and_assurance_require_explicit_invocation(self) -> None:
        for name in ("forge-loop", "forge-assurance"):
            with self.subTest(skill=name):
                self.assertEqual(
                    "true",
                    frontmatter(name).get("disable-model-invocation"),
                )
                sidecar = (SKILLS / name / "agents/openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("allow_implicit_invocation: false", sidecar)

    def test_all_nine_skills_are_still_packaged(self) -> None:
        self.assertEqual(
            PUBLIC_SKILLS | INTERNAL_SKILLS,
            {path.name for path in SKILLS.iterdir() if path.is_dir()},
        )


if __name__ == "__main__":
    unittest.main()
