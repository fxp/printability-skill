from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import trimesh
import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_mesh.py"
VALUE_CASES = {
    case["id"]: case
    for case in yaml.safe_load((ROOT / "evals" / "value-cases.yaml").read_text(encoding="utf-8"))["cases"]
}


class AuditMeshTests(unittest.TestCase):
    def assert_expected_axes(self, case_id: str, report: dict, variant: str | None = None) -> None:
        case = VALUE_CASES[case_id]
        if variant is None:
            expected = case["expected_axes"]
        else:
            expected = next(
                item["expected_axes"] for item in case["variants"] if item["name"] == variant
            )
        for axis, status in expected.items():
            self.assertEqual(report[axis], status, f"{case_id} {variant or 'default'} {axis}")

    def run_audit(self, mesh: Path, *arguments: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(AUDITOR), str(mesh), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertTrue(result.stdout, result.stderr)
        report = json.loads(result.stdout)
        if result.returncode == 2:
            self.fail(report.get("error", "mesh auditor returned an input/runtime error"))
        return result.returncode, report

    def test_closed_solid_passes_static_gate_but_not_function(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "cube.stl"
            trimesh.creation.box(extents=(20, 10, 5)).export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "solid",
                "--process", "fdm",
            )

        self.assertEqual(code, 0)
        self.assert_expected_axes("PRT-001", report)

    def test_open_solid_fails_watertight_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "open.stl"
            mesh = trimesh.creation.box(extents=(20, 10, 5))
            mesh.update_faces([False] + [True] * (len(mesh.faces) - 1))
            mesh.remove_unreferenced_vertices()
            mesh.export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "solid",
            )

        self.assertEqual(code, 1)
        self.assert_expected_axes("PRT-002", report, "closed-solid-intent")
        self.assertIn("not_watertight_for_closed_volume_intent", report["blockers"])

    def test_open_surface_is_allowed_conditionally(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "surface.stl"
            mesh = trimesh.creation.box(extents=(20, 10, 5))
            mesh.update_faces([False] + [True] * (len(mesh.faces) - 1))
            mesh.remove_unreferenced_vertices()
            mesh.export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "surface",
            )

        self.assertEqual(code, 0)
        self.assert_expected_axes("PRT-002", report, "explicit-surface-intent")
        self.assertEqual(report["overall"], "conditional")
        self.assertTrue(any("Open boundaries" in note for note in report["notes"]))

    def test_expected_shell_count_and_axis_aligned_fit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "pair.stl"
            first = trimesh.creation.box(extents=(30, 10, 5))
            second = trimesh.creation.box(extents=(30, 10, 5))
            second.apply_translation((50, 0, 0))
            trimesh.util.concatenate([first, second]).export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "multipart",
                "--expect-shells", "2",
                "--build-volume", "15", "90", "10",
                "--fit-mode", "axis-aligned",
            )

        self.assertEqual(code, 0)
        self.assertEqual(report["connected_shells"], 2)
        self.assertTrue(report["build_volume_check"]["fits_any_axis_aligned_orientation"])

    def test_unexpected_fragment_fails_declared_shell_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "kit-with-fragment.stl"
            parts = []
            for index in range(4):
                part = trimesh.creation.box(extents=(10, 10, 10))
                part.apply_translation((index * 20, 0, 0))
                parts.append(part)
            fragment = trimesh.creation.box(extents=(0.2, 0.2, 0.2))
            fragment.apply_translation((90, 0, 0))
            trimesh.util.concatenate([*parts, fragment]).export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "multipart",
                "--expect-shells", "4",
            )
            risk_code, risk_report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "multipart",
            )

        self.assertEqual(code, 1)
        self.assert_expected_axes("PRT-003", report)
        self.assertEqual(report["connected_shells"], 5)
        self.assertIn("unexpected_connected_shell_count", report["blockers"])
        self.assertEqual(risk_code, 0)
        self.assertEqual(risk_report["geometry_gate"], "pass")
        self.assertIn("multiple_shells_require_design_intent_review", risk_report["risks"])

    def test_reversed_winding_fails_signed_volume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "inside-out.stl"
            mesh = trimesh.creation.box(extents=(20, 10, 5))
            mesh.invert()
            mesh.export(model)
            code, report = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "solid",
            )

        self.assertEqual(code, 1)
        self.assertTrue(report["winding_consistent"])
        self.assertLess(report["signed_volume_mm3"], 0)
        self.assertIn("nonpositive_or_nonfinite_signed_volume", report["blockers"])

    def test_rotation_can_recover_build_volume_fit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "rotatable.stl"
            trimesh.creation.box(extents=(250, 280, 10)).export(model)
            current_code, current = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "solid",
                "--build-volume", "256", "256", "300",
                "--fit-mode", "current",
            )
            rotated_code, rotated = self.run_audit(
                model,
                "--unit", "mm",
                "--intent", "solid",
                "--build-volume", "256", "256", "300",
                "--fit-mode", "axis-aligned",
            )

        self.assertEqual(current_code, 1)
        self.assertFalse(current["build_volume_check"]["fits"])
        self.assertEqual(rotated_code, 0)
        self.assert_expected_axes("PRT-005", rotated)
        self.assertTrue(rotated["build_volume_check"]["fits_any_axis_aligned_orientation"])
        self.assertIn([250.0, 10.0, 280.0], rotated["build_volume_check"]["fitting_axis_aligned_extents_mm"])


if __name__ == "__main__":
    unittest.main()
