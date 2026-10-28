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

    def test_value_eval_suite_contract(self) -> None:
        suite = yaml.safe_load((ROOT / "evals" / "value-cases.yaml").read_text(encoding="utf-8"))
        self.assertEqual(suite["version"], 1)
        self.assertEqual(suite["suite"], "printability-value-cases")
        self.assertGreaterEqual(len(suite["global_acceptance"]), 5)
        self.assertTrue(suite["evidence_scope"].strip())

        cases = suite["cases"]
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertEqual(
            {case["layer"] for case in cases},
            {"automated-auditor", "manual-skill-acceptance"},
        )

        vocabulary = suite["status_vocabulary"]
        report_contract = (ROOT / "references" / "report-contract.md").read_text(encoding="utf-8")
        for field, statuses in vocabulary.items():
            match = re.search(rf"^{field}: ([a-z_ |]+)$", report_contract, re.MULTILINE)
            self.assertIsNotNone(match, field)
            contract_statuses = {status.strip() for status in match.group(1).split("|")}
            self.assertEqual(set(statuses), contract_statuses, field)

        audit_test_source = (ROOT / "tests" / "test_audit_mesh.py").read_text(encoding="utf-8")
        value_guide = (ROOT / "VALUE_CASES.md").read_text(encoding="utf-8")
        for case in cases:
            self.assertRegex(case["id"], r"^PRT-\d{3}$")
            self.assertEqual(value_guide.count(case["id"]), 1)
            self.assertTrue(case["prompt"].strip())
            self.assertTrue(case["value"].strip())
            self.assertGreaterEqual(len(case["must_include"]), 2)
            self.assertGreaterEqual(len(case["must_not_claim"]), 1)
            self.assertNotEqual("expected_axes" in case, "variants" in case)

            if case["layer"] == "automated-auditor":
                self.assertGreaterEqual(len(case["automation_tests"]), 1)
                for test_name in case["automation_tests"]:
                    self.assertIn(f"def {test_name}(", audit_test_source, f"{case['id']} {test_name}")
            else:
                self.assertNotIn("automation_tests", case)

            axis_sets = [case["expected_axes"]] if "expected_axes" in case else [
                variant["expected_axes"] for variant in case["variants"]
            ]
            if "variants" in case:
                self.assertGreaterEqual(len(case["variants"]), 2)
                self.assertEqual(
                    len({variant["name"] for variant in case["variants"]}),
                    len(case["variants"]),
                )
            for axes in axis_sets:
                self.assertEqual(set(axes), set(vocabulary))
                for field, status in axes.items():
                    self.assertIn(status, vocabulary[field], f"{case['id']} {field}")


if __name__ == "__main__":
    unittest.main()
