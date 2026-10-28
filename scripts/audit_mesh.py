#!/usr/bin/env python3
"""Audit STL/OBJ/PLY geometry without modifying the source.

Exit 0 means the static geometry gate passed for the declared intent.
Exit 1 means a proved static blocker was found. Exit 2 means input/runtime error.
Static success is only permission to continue to source and slicer validation.
"""

from __future__ import annotations

import argparse
from itertools import permutations
import json
import math
from pathlib import Path
import sys
from typing import Any


UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "inch": 25.4}


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return number


def nonnegative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite nonnegative number")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def add_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def build_volume_result(np: Any, extents: Any, build: list[float], fit_mode: str) -> dict[str, Any]:
    build_array = np.asarray(build, dtype=float)
    current = bool((extents <= build_array + 1e-8).all())
    result: dict[str, Any] = {
        "build_size_mm": build,
        "fits_current_orientation_allowing_translation": current,
        "fit_mode": fit_mode,
        "excluded": ["machine_keepouts", "skirt_or_raft", "supports", "multi_part_layout", "toolhead_collision"],
    }
    if fit_mode == "axis-aligned":
        orientations = sorted({tuple(float(x) for x in p) for p in permutations(extents.tolist())})
        fitting = [list(p) for p in orientations if bool((np.asarray(p) <= build_array + 1e-8).all())]
        result["fits_any_axis_aligned_orientation"] = bool(fitting)
        result["fitting_axis_aligned_extents_mm"] = fitting
        result["fits"] = bool(fitting)
    else:
        result["fits"] = current
    return result


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import numpy as np
        import trimesh
    except ImportError as exc:
        raise RuntimeError("Use a Python environment with trimesh and numpy: " + str(exc)) from exc

    source = args.mesh.expanduser().resolve()
    if not source.is_file():
        raise ValueError("Input file does not exist: " + str(source))
    if source.suffix.lower() not in {".stl", ".obj", ".ply"}:
        raise ValueError("Only STL/OBJ/PLY are supported; inspect 3MF and CAD formats in their native tools")

    loaded = trimesh.load(str(source), force="mesh", process=False)
    if not isinstance(loaded, trimesh.Trimesh):
        raise ValueError("Input did not load as one triangle mesh")

    mesh = loaded.copy()
    blockers: list[str] = []
    risks: list[str] = []
    notes: list[str] = []
    report: dict[str, Any] = {
        "file": str(source),
        "scope": "static_mesh_gate_only",
        "geometry_intent": args.intent,
        "functional_intent": "unknown",
        "process": args.process,
        "declared_input_unit": args.unit,
        "report_unit": "mm",
        "trimesh_version": trimesh.__version__,
        "preprocessing": "in-memory unit conversion and vertex welding at 8 decimal places in mm; no source write or repair",
        "blockers": blockers,
        "risks": risks,
        "notes": notes,
        "not_evaluated": [
            "self_intersections_and_coplanar_overlaps",
            "minimum_wall_thickness",
            "minimum_features_and_holes",
            "assembly_clearance_and_fit",
            "overhangs_bridges_islands_and_support_removal",
            "drainage_venting_powder_escape_and_suction",
            "warping_shrinkage_and_strength",
            "slicer_layers_and_machine_keepouts",
            "physical_fit_and_function",
        ],
    }

    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        add_once(blockers, "empty_mesh")
        report.update({
            "geometry_gate": "fail",
            "process_feasibility": "unknown",
            "functional_validation": "unknown",
            "quality_risk": "unknown",
            "overall": "blocked",
            "evidence_level": "static",
        })
        return report

    mesh.apply_scale(UNIT_TO_MM[args.unit])
    if not np.isfinite(mesh.vertices).all():
        add_once(blockers, "non_finite_coordinates")
        report.update({
            "geometry_gate": "fail",
            "process_feasibility": "unknown",
            "functional_validation": "unknown",
            "quality_risk": "unknown",
            "overall": "blocked",
            "evidence_level": "static",
        })
        return report
    if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
        add_once(blockers, "invalid_face_indices")
        report.update({
            "geometry_gate": "fail",
            "process_feasibility": "unknown",
            "functional_validation": "unknown",
            "quality_risk": "unknown",
            "overall": "blocked",
            "evidence_level": "static",
        })
        return report

    original_vertices = len(mesh.vertices)
    mesh.merge_vertices(digits_vertex=8)
    edge_counts = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique))
    degenerate = int((~mesh.nondegenerate_faces(height=1e-8)).sum())
    duplicate = int(len(mesh.faces) - mesh.unique_faces().sum())
    components = mesh.split(only_watertight=False)
    watertight = bool(mesh.is_watertight)
    winding = bool(mesh.is_winding_consistent)
    raw_volume = float(mesh.volume)
    volume = raw_volume if math.isfinite(raw_volume) else None
    extents = np.asarray(mesh.extents, dtype=float)
    boundary_edges = int((edge_counts == 1).sum())
    nonmanifold_edges = int((edge_counts > 2).sum())

    component_summary = []
    for component in components:
        component_summary.append({
            "triangles": int(len(component.faces)),
            "size_mm": [float(x) for x in component.extents],
            "watertight": bool(component.is_watertight),
        })
    component_summary.sort(key=lambda item: item["triangles"], reverse=True)

    report.update({
        "vertices_before_welding": int(original_vertices),
        "vertices": int(len(mesh.vertices)),
        "triangles": int(len(mesh.faces)),
        "bounds_mm": [[float(x) for x in row] for row in mesh.bounds],
        "size_mm": [float(x) for x in extents],
        "surface_area_mm2": float(mesh.area),
        "connected_shells": int(len(components)),
        "shells": component_summary,
        "boundary_edges": boundary_edges,
        "nonmanifold_edges": nonmanifold_edges,
        "degenerate_faces": degenerate,
        "duplicate_faces": duplicate,
        "watertight": watertight,
        "winding_consistent": winding,
        "signed_volume_mm3": volume,
        "volume_is_meaningful": args.intent in {"solid", "multipart"} and watertight and winding and volume is not None and volume > 0,
    })

    if nonmanifold_edges:
        add_once(blockers, "nonmanifold_edges")
    if args.intent in {"solid", "multipart"}:
        if not watertight:
            add_once(blockers, "not_watertight_for_closed_volume_intent")
        if not winding:
            add_once(blockers, "inconsistent_face_winding_for_closed_volume_intent")
        if volume is None or volume <= 0:
            add_once(blockers, "nonpositive_or_nonfinite_signed_volume")
    else:
        if not watertight:
            add_once(notes, "Open boundaries are allowed by the declared surface intent but require explicit slicer surface or wall generation")
        if not winding:
            add_once(risks, "inconsistent_face_winding")

    if degenerate:
        add_once(risks, "degenerate_faces")
    if duplicate:
        add_once(risks, "duplicate_faces")
    if len(components) > 1 and args.expect_shells is None:
        add_once(risks, "multiple_shells_require_design_intent_review")
    if args.expect_shells is not None:
        report["expected_connected_shells"] = args.expect_shells
        if len(components) != args.expect_shells:
            add_once(blockers, "unexpected_connected_shell_count")

    if args.expect_size is not None:
        expected = np.asarray(args.expect_size, dtype=float)
        delta = np.abs(extents - expected)
        report["expected_size_mm"] = args.expect_size
        report["size_error_mm"] = [float(x) for x in delta]
        report["size_tolerance_mm"] = args.size_tolerance
        if bool((delta > args.size_tolerance).any()):
            add_once(blockers, "size_mismatch")

    if args.build_volume is not None:
        fit = build_volume_result(np, extents, args.build_volume, args.fit_mode)
        report["build_volume_check"] = fit
        if not fit["fits"]:
            add_once(blockers, "does_not_fit_declared_build_volume")

    report["geometry_gate"] = "fail" if blockers else "pass"
    report["overall"] = "blocked" if blockers else "conditional"
    report["process_feasibility"] = "unknown"
    report["functional_validation"] = "unknown"
    report["quality_risk"] = "unknown"
    report["evidence_level"] = "static"
    report["interpretation"] = (
        "Static geometry has blockers; repair or clarify intent before process validation."
        if blockers
        else "Static gate passed for the declared intent; actual slicing and physical validation are still required."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh", type=Path)
    parser.add_argument("--unit", required=True, choices=UNIT_TO_MM, help="Explicit coordinate unit; never guessed")
    parser.add_argument("--intent", required=True, choices=("solid", "surface", "multipart"))
    parser.add_argument("--process", default="unknown", choices=("unknown", "fdm", "resin", "powder", "metal"))
    parser.add_argument("--expect-size", type=positive_float, nargs=3, metavar=("X_MM", "Y_MM", "Z_MM"))
    parser.add_argument("--size-tolerance", type=nonnegative_float, default=0.1)
    parser.add_argument("--expect-shells", type=positive_int)
    parser.add_argument("--build-volume", type=positive_float, nargs=3, metavar=("X_MM", "Y_MM", "Z_MM"))
    parser.add_argument("--fit-mode", default="current", choices=("current", "axis-aligned"))
    parser.add_argument("--output", type=Path, help="Optional JSON report; must not overwrite the input")
    args = parser.parse_args()

    if args.output and args.output.expanduser().resolve() == args.mesh.expanduser().resolve():
        parser.error("--output must not overwrite the source model")
    try:
        report = analyze(args)
        code = 0 if report["geometry_gate"] == "pass" else 1
        output = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    except Exception as exc:
        output = json.dumps({
            "geometry_gate": "unknown",
            "process_feasibility": "unknown",
            "functional_validation": "unknown",
            "quality_risk": "unknown",
            "overall": "error",
            "scope": "static_mesh_gate_only",
            "error": str(exc),
        }, ensure_ascii=False, indent=2)
        code = 2

    if args.output:
        try:
            target = args.output.expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(output + "\n", encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"overall": "error", "error": "Cannot write report: " + str(exc)}))
            return 2
    print(output)
    return code


if __name__ == "__main__":
    sys.exit(main())
