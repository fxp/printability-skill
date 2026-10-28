# Printability value demonstration cases

These cases test whether the Skill makes the right decision, not whether it repeats expected wording. Exact prompts, five-axis expectations, required findings, and prohibited claims live only in the canonical machine-readable file: [`evals/value-cases.yaml`](evals/value-cases.yaml).

This page is explanatory, not a second grading contract.

## How the suite is split

- `automated-auditor`: backed by named methods in `tests/test_audit_mesh.py`; CI executes the geometry behavior.
- `manual-skill-acceptance`: a structured prompt and expected decision for evaluating the full Skill, including source, process, and function reasoning that the static auditor cannot prove.

## Cases and value

| ID | Scenario | Failure caught | Why it matters |
| --- | --- | --- | --- |
| PRT-001 | Clean watertight cube with only static STL evidence | Declaring the part printable or functional | A valid mesh is not a validated machine setup or product. |
| PRT-002 | The same open lampshade reviewed as a solid and as an explicit surface | Applying one unconditional watertight rule | Geometry intent changes whether an open boundary is a blocker. |
| PRT-003 | Four intended parts plus one tiny disconnected fragment | Rejecting every multipart model, or missing export debris | Shell count only has meaning relative to design intent. |
| PRT-004 | Reversed triangle winding versus broken smoothing normals | Treating both as the same normal defect | One changes solid inside/outside semantics; the other usually changes preview only. |
| PRT-005 | Part that fits only after an allowed axis-aligned rotation | Rejecting the imported orientation as too large | Orientation can remove a false build-volume blocker. |
| PRT-006 | Watertight hollow resin shell with no drain or vent path | Calling a manifold shell resin-ready | Process-specific suction, trapped resin, cleaning, and curing can still fail. |
| PRT-007 | Watertight bottle and cap with incompatible threads | Equating individually sliceable parts with a working assembly | Product function requires pitch, clearance, engagement, and stop checks. |
| PRT-008 | Phone-case relief visible only in a normal map | Assuming rendered texture becomes raised material | Printed relief requires actual displaced geometry. |
| PRT-009 | Sliceable print-in-place hinge below a calibrated clearance | Treating generated paths as proof of motion | Machine/material calibration can prove a joint will fuse before a full print. |
| PRT-010 | Unitless 1 × 1 × 1 STL with no known dimension | Silently guessing millimetres or inches | A unit guess can create a 25.4× scale failure. |

## Passing the suite

A result must keep geometry, process, function, quality, and evidence separate. It must preserve blockers and unknowns, identify the smallest useful next validation step, and avoid claiming printability from static evidence alone. External upload, remote slicing, and hardware operation remain outside scope without explicit authorization.
