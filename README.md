# Printability Skill

A Codex skill for reviewing whether a 3D model is ready to enter an additive-manufacturing workflow.

It deliberately avoids a single “printability score.” Reports keep five conclusions separate:

- `geometry_gate`: whether the declared geometry intent has a proved blocker
- `process_feasibility`: whether the target machine, material, orientation, support, and slicer setup are viable
- `functional_validation`: whether assembly, motion, fit, enclosure, fluid, thread, or other intended behavior is validated
- `quality_risk`: expected surface, dimensional, and functional quality risk
- `evidence_level`: `static`, `source`, `sliced`, or `physical`

The included deterministic auditor supports STL, OBJ, and PLY. It never modifies the source model and never treats a static pass as proof that a part will slice or work physically.

## Highlights

- Context-aware watertight, manifold, face-winding, shell-count, and build-volume checks
- Separate treatment of render normals and triangle winding
- Process-specific guidance for FDM/FFF, resin, powder, and metal workflows
- Functional-intent routes for assemblies, joints, enclosures, lamps, containers, fluid paths, threaded closures, reliefs, and layered laser-cut work
- A report contract that preserves hard blockers and unknowns instead of averaging them into a score
- Safety boundaries for repair, upload, slicing, and printer operation

## Install

Clone the repository into your Codex skills directory:

```bash
git clone https://github.com/fxp/printability-skill.git ~/.codex/skills/printability
python -m pip install -r ~/.codex/skills/printability/requirements.txt
```

Restart or reload the Codex skill inventory, then invoke `$printability` with a model and its intended process and function.

## Static mesh audit

```bash
python scripts/audit_mesh.py part.stl \
  --unit mm \
  --intent solid \
  --process fdm \
  --build-volume 256 256 256 \
  --fit-mode axis-aligned
```

Exit codes:

- `0`: the static geometry gate passed for the declared intent
- `1`: a proved static geometry blocker was found
- `2`: input, dependency, or runtime error

Static success only means the model may proceed to source and slicer validation.

## Tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The [value demonstration suite](VALUE_CASES.md) contains ten acceptance cases that show why geometry-only checks are insufficient. The same cases are available in machine-readable form at [`evals/value-cases.yaml`](evals/value-cases.yaml).

## Hi3D research note

The functional-intent taxonomy in [`references/functional-intent-routes.md`](references/functional-intent-routes.md) was informed by public descriptions in the [Hi3D Agent 3D Printing category](https://www.hi3d.ai/agent?category=3d-printing), reviewed on 2026-10-28. It does not reproduce or claim access to Hi3D's internal prompts, implementation, or validation criteria. This project is not affiliated with or endorsed by Hi3D.

## License

[MIT](LICENSE)
