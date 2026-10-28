from __future__ import annotations

from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_and_agent_metadata(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        metadata = yaml.safe_load(match.group(1))
        self.assertEqual(metadata["name"], "printability")
        self.assertIn("3D", metadata["description"])

        agent = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(agent["interface"]["display_name"], "Printability")

    def test_linked_local_references_exist(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\((references/[^)]+)\)", text)
        self.assertGreaterEqual(len(links), 4)
        for link in links:
            self.assertTrue((ROOT / link).is_file(), link)

    def test_all_public_hi3d_printing_skill_ids_are_mapped(self) -> None:
        reference = (ROOT / "references" / "functional-intent-routes.md").read_text(encoding="utf-8")
        expected = {
            "lamp-design", "twisty-fidget", "multiview-parts", "relief-brush",
            "layered-laser-ornament", "print-joints", "image-to-assembly",
            "motion-base", "frame-design", "relief-box", "teapot-design",
            "vase-design", "water-feature", "print-kit", "product-design",
            "articulated-sculpture", "device-enclosure", "sculpture-container",
            "screw-bottle", "phone-case-relief",
        }
        missing = sorted(skill_id for skill_id in expected if skill_id not in reference)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
