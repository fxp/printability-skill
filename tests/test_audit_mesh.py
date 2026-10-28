from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import trimesh


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_mesh.py"


class AuditMeshTests(unittest.TestCase):
    def run_audit(self, mesh: Path, *arguments: str) -> tuple[int, dict]:
        result = subprocess.run(
            [sys.executable, str(AUDITOR), str(mesh), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertTrue(result.stdout, result.stderr)
        return result.returncode, json.loads(result.stdout)

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
        self.assertEqual(report["geometry_gate"], "pass")
        self.assertEqual(report["process_feasibility"], "unknown")
        self.assertEqual(report["functional_validation"], "unknown")
        self.assertEqual(report["quality_risk"], "unknown")
        self.assertEqual(report["evidence_level"], "static")

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
        self.assertEqual(report["geometry_gate"], "fail")
        self.assertIn("not_watertight_for_closed_volume_intent", report["blockers"])
        self.assertEqual(report["functional_validation"], "unknown")

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
        self.assertEqual(report["geometry_gate"], "pass")
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


if __name__ == "__main__":
    unittest.main()
