from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProductBoundaryTests(unittest.TestCase):
    def test_obsolete_compatibility_and_history_surfaces_are_absent(self):
        removed = [
            ROOT / "install.sh",
            ROOT / "plugins/forge/scripts/forge-migrate",
            ROOT / "plugins/forge/scripts/validate-intent",
            ROOT / "plugins/forge/docs/DOCTRINE.md",
            ROOT / "plugins/forge/docs/AGENTS-BRIDGE.md",
            ROOT / "tests/fixtures/legacy_forge",
            ROOT / "tests/test_forge_migrate.py",
            ROOT / "tests/test_install.py",
            ROOT / "tests/test_dogfood_scorecards.py",
            ROOT / "docs/archive",
            ROOT / "docs/superpowers",
            ROOT / "docs/dogfood",
            ROOT / "scripts/summarize-memory-first-dogfood.py",
        ]

        self.assertEqual([], [str(path) for path in removed if path.exists()])

if __name__ == "__main__":
    unittest.main()
