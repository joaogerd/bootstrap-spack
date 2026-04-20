# Release Checklist — 1.0.0

## Objective

This document defines the practical release gate for `bootstrap-spack` to move from the current `0.4.x` line to a stable `1.0.0` release and then transition into real production-oriented operation.

The goal is not to keep redesigning the architecture.
The goal is to close the public contract of the tool, strengthen end-to-end confidence, and make the project safe to use as a real institutional bootstrap utility.

---

## Current situation

The `0.4.1` line already established an important foundation:

- explicit separation between detected facts and derived policy
- platform facts modeled explicitly
- policy-aware rendering of artifacts
- configurable site external promotion behavior
- layered site generation
- passing automated test suite
- updated README, user manual and changelog

This means the project is no longer in an early structural phase.

What remains before `1.0.0` is mainly:

- closing the public contract
- strengthening product-level validation
- finishing the operational documentation

---

## A. Mandatory for 1.0.0

### 1. Public contract of the project

- [ ] Define the official support scope
  - [ ] generic Linux
  - [ ] cluster with Lmod / Environment Modules
  - [ ] Cray-like / JACI
  - [ ] EGEON
- [ ] Define the officially supported package set
  - [ ] openmpi
  - [ ] mpich
  - [ ] hdf5
  - [ ] netcdf-c
  - [ ] netcdf-fortran
- [ ] Define what is considered stable in `1.x`
  - [ ] YAML configuration schema
  - [ ] generated artifact structure
  - [ ] facts / policy / authority / trace semantics
  - [ ] `external_promotion_mode` behavior

### 2. Configuration contract closed

- [ ] Review all YAML fields and decide which ones are part of the stable public API
- [ ] Freeze names and semantics of:
  - [ ] `platform`
  - [ ] `modules.load`
  - [ ] `modules.optional`
  - [ ] `packages.external`
  - [ ] `validation.strict`
  - [ ] `site.*`
  - [ ] `template.*`
  - [ ] `site.policy_overrides.*`
  - [ ] `site.external_promotion_mode`
- [ ] Guarantee validation coverage and clear error messages for invalid configuration fields

### 3. Generated artifact contract closed

- [ ] Freeze the minimum supported output structure:
  - [ ] `packages.yaml`
  - [ ] `detection-report.txt`
  - [ ] `configs/common/packages.yaml`
  - [ ] `configs/common/modules.yaml`
  - [ ] `configs/sites/<site>/packages.yaml`
  - [ ] `configs/sites/<site>/compilers.yaml`
  - [ ] `configs/sites/<site>/modules.yaml`
  - [ ] `configs/sites/<site>/config.yaml`
  - [ ] `configs/templates/<template>/spack.yaml`
- [ ] Document what is guaranteed versus what remains heuristic
- [ ] Explicitly document the difference between unified output and layered output

### 4. Full product-level testing

- [ ] Keep the existing automated suite green
- [ ] Add end-to-end fixture-based validation for complete generated outputs
  - [ ] Linux simple case without modules
  - [ ] EGEON case
  - [ ] JACI / Cray-like case
  - [ ] `external_promotion_mode: all`
  - [ ] `external_promotion_mode: providers-only`
  - [ ] explicit `policy_overrides.platform.target`
- [ ] Add regression tests for the major 0.4.x bugfixes
- [ ] Validate full YAML outputs, not only internal helper behavior

### 5. Minimum operational documentation

- [ ] Keep `README.md` aligned with shipped behavior
- [ ] Keep `docs/user-manual.md` aligned with shipped behavior
- [ ] Add `docs/how-to-add-a-new-machine.md`
- [ ] Add `docs/how-to-read-detection-report.md`
- [ ] Add `docs/when-to-use-overrides.md`
- [ ] Add a short decision guide for:
  - [ ] `external_promotion_mode: all`
  - [ ] `external_promotion_mode: providers-only`

### 6. Final semantic closure for platform policy

- [ ] Confirm as stable rule that detected host facts are distinct from final site policy
- [ ] Confirm as stable rule that institutional targets such as `core2` are policy, not detected facts
- [ ] Confirm that normalized OS values such as `rhel8` are the final site policy values, not raw distro strings such as `rhel8.4`
- [ ] Confirm that final renderers consume policy values rather than heuristic compiler metadata shortcuts

---

## B. Strongly recommended before 1.0.0

### 7. Naming review

- [ ] Review field and model names to ensure they are final-quality public names
- [ ] Check consistency across:
  - [ ] domain models
  - [ ] config loader
  - [ ] renderers
  - [ ] README
  - [ ] user manual
  - [ ] changelog
- [ ] Remove or rename terms that still feel compatibility-oriented instead of semantically final

### 8. Operational robustness

- [ ] Review failure handling for:
  - [ ] missing modules
  - [ ] missing binaries
  - [ ] inconsistent wrappers
  - [ ] partial validation
  - [ ] incomplete specs
- [ ] Ensure degradation paths remain honest and auditable
- [ ] Review CLI messages for real operational use

### 9. Detection report quality

- [ ] Review `detection-report.txt` as a real operational artifact
- [ ] Ensure it clearly shows:
  - [ ] detected facts
  - [ ] final policy
  - [ ] overrides applied
  - [ ] authority
  - [ ] trace
  - [ ] warnings
- [ ] Ensure the report is sufficient to debug a new machine onboarding

### 10. Real machine validation set

- [ ] Archive or document validated outputs for:
  - [ ] EGEON
  - [ ] JACI
  - [ ] Linux local no-modules case
- [ ] Manually inspect generated YAML files for these cases before the 1.0.0 release
- [ ] Document support status per machine profile

---

## C. Useful, but not blocking 1.0.0

### 11. Example configurations

- [ ] Expand the `env/` examples with more explicit use cases
  - [ ] `linux_minimal.yaml`
  - [ ] `egeon.yaml`
  - [ ] `jaci.yaml`
  - [ ] `providers_only.yaml`
  - [ ] `all_externals.yaml`

### 12. Support and rationale docs

- [ ] Add a short support matrix document
- [ ] Add a short known-limitations document
- [ ] Add a short design rationale document if useful for maintainers

### 13. Release quality discipline

- [ ] Keep changelog precise and auditable
- [ ] Keep version bump process clean
- [ ] Keep tags and release notes aligned with shipped behavior
- [ ] Ensure docs and examples always match the released version

---

## Practical release gate

The project is ready for `1.0.0` when all of the following are true:

- [ ] configuration contract is frozen
- [ ] generated artifact contract is frozen
- [ ] end-to-end fixture validation is green
- [ ] minimum operational documentation is complete
- [ ] Linux, EGEON and JACI cases are validated
- [ ] no relevant ambiguity remains between detection and policy semantics

---

## After 1.0.0

Once `1.0.0` is closed, the project focus should shift from architectural stabilization to real production operation.

That next phase should prioritize:

- onboarding of new machines
- institutional workflows
- operational hardening
- broader package coverage
- production-oriented support discipline

---

## Summary

The remaining path to `1.0.0` is not mainly about large refactors.

It is mainly about:

- closing the public contract
- validating the product end-to-end
- finishing the operational documentation

That is the right bridge between the current `0.4.x` maturity and a real `1.0.0` release ready for production-facing use.
