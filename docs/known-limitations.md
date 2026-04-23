# Known Limitations

## Purpose

This document records the current known limitations of `bootstrap-spack` in an explicit way.

This is important for two reasons:

1. it helps maintainers and users avoid treating heuristics as guarantees;
2. it helps define an honest release boundary for the path to `1.0.0`.

A limitation is not automatically a defect.
Many limitations are simply boundaries of the current product scope.

---

## 1. Focused package support

The project currently focuses on a narrow, intentional package set:

- MPI (`openmpi`, `mpich`)
- `hdf5`
- `netcdf-c`
- `netcdf-fortran`

This means:

- the project is not a general detector for arbitrary HPC software stacks yet;
- support for packages outside this set should be treated as out of scope unless explicitly added.

---

## 2. Compiler and toolchain inference still include heuristics

Even though the project has become much more explicit semantically, some compiler and toolchain decisions still rely on heuristics.

Examples:

- wrapper-based inference in complex environments
- environment-dependent compiler path interpretation
- partial reliance on site behavior when wrappers do not expose clean metadata

Practical consequence:

- detection reports and generated artifacts should still be reviewed on new machines;
- complex HPC environments should not be treated as fully self-explanatory from detection alone.

---

## 3. Module behavior remains site-dependent

Module systems are one of the biggest sources of machine-specific behavior.

Typical sources of variation include:

- different module names
- different module hierarchy rules
- unexpected fallback modules
- environment contamination from previously loaded modules

Practical consequence:

- module selection remains an operational responsibility of the user or site maintainer;
- a wrong module environment can still produce technically valid but semantically wrong outputs.

---

## 4. Detection quality depends on execution environment quality

The tool is honest about what it sees, but it cannot magically fix a bad environment.

If the execution environment is wrong, typical consequences include:

- wrong tool detected first in `PATH`
- wrong wrapper used
- wrong prefix captured
- mixed toolchain evidence

Practical consequence:

- `detection-report.txt` must still be inspected on new machines;
- overrides should not be used as a substitute for fixing the environment.

---

## 5. Unified output and layered output serve different purposes

The root `packages.yaml` and the layered site outputs are related, but they do not serve exactly the same purpose.

Typical distinction:

- root `packages.yaml` is oriented toward direct Spack use;
- `configs/sites/<site>/packages.yaml` is a site-policy artifact.

Practical consequence:

- users should not assume that every policy choice is identical across both outputs;
- site-level external promotion behavior is intentionally configurable.

---

## 6. `external_promotion_mode` is intentionally narrow

The current line supports only:

- `all`
- `providers-only`

This is a deliberate simplification.

Practical consequence:

- more sophisticated package-promotion strategies are not yet part of the public product contract;
- if future use cases demand more modes, that should be treated as an intentional feature expansion, not as assumed current behavior.

---

## 7. Real-machine validation is still essential

The project has automated tests and real-machine validation, but real environments still matter heavily.

Practical consequence:

- a passing test suite is necessary, but not sufficient, for declaring a new machine operationally supported;
- generated YAML files should still be reviewed and used in the real target workflow.

---

## 8. The project is not a replacement for all manual judgment

The tool improves repeatability and auditability, but it does not eliminate the need for site judgment.

Typical decisions that still require human intent include:

- whether to use a conservative target override
- whether to use `all` or `providers-only`
- whether runtime paths should be overridden institutionally
- whether a detected stack should really be mirrored into site policy

Practical consequence:

- `bootstrap-spack` is a decision-supporting bootstrap tool, not an autonomous site-policy oracle.

---

## 9. Broader ecosystem coverage is not yet a goal of the current line

The current line is optimized for a focused HPC/scientific software workflow.

Practical consequence:

- future package expansion should be deliberate and tested;
- the 1.0.0 release should stay honest about the current support boundary instead of overstating generality.

---

## 10. Some semantics are now stable, but still need release-level discipline

The internal architecture is much stronger than in earlier versions, but `1.0.0` still requires discipline around:

- frozen public config semantics
- frozen artifact semantics
- explicit support scope
- documented operational workflow

Practical consequence:

- the project is close to a stable release line, but should avoid pretending that every possible behavior is already a public guarantee.

---

## Summary

The current limitations can be summarized like this:

- package scope is intentionally focused
- some environment and toolchain behavior remain heuristic
- module environments remain site-sensitive
- real-machine validation still matters
- human policy judgment is still required

These limitations do not prevent `bootstrap-spack` from being useful.
They simply define the honest boundary of the current product.
