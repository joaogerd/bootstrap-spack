# Support Matrix

## Purpose

This document defines the current support scope of `bootstrap-spack` and gives a practical interpretation of what kinds of environments are considered:

- validated in real usage
- validated by automated tests
- heuristic but intentionally supported
- out of scope for the current release line

This matrix is important for the path to `1.0.0` because the project should not claim more support than it can justify.

---

## Support status levels

### Validated in real environment

The behavior has been exercised on an actual machine or cluster and inspected in practice.

### Validated by automated tests

The behavior is covered by the test suite, but not necessarily exercised recently on a real target machine.

### Heuristic support

The code is intentionally designed for the environment class, but behavior still depends on site-specific assumptions and should be treated carefully.

### Out of scope

The environment is not a target of the current release line.

---

## Environment classes

### 1. Generic Linux without modules

**Status:** validated by automated tests and real local usage

**Scope:** supported

Typical characteristics:

- no module system required
- direct discovery from `PATH`
- local compiler and library tools

Expected use:

- simple external detection
- direct Spack `packages.yaml` generation
- baseline layered site generation for local experiments

Notes:

- this is one of the cleanest environments for debugging behavior
- useful as a baseline regression target

---

### 2. Cluster with Lmod or Environment Modules

**Status:** validated in real environment

**Scope:** supported

Typical characteristics:

- explicit base modules
- optional fallback modules
- site-specific wrapper and prefix layout

Expected use:

- package detection through module-loaded toolchains
- layered site generation
- provider-aware site policy derivation

Notes:

- environment contamination still matters a lot
- module selection quality strongly influences results

---

### 3. EGEON-style environment

**Status:** validated in real environment

**Scope:** supported

Typical characteristics:

- module-driven compiler and MPI stack
- site-oriented layered generation
- real use against `spack-stack`-style workflows

Expected use:

- normalized platform policy generation
- configurable external promotion behavior
- conservative `providers-only` site output when desired

Notes:

- this is currently one of the main practical reference environments for the project
- especially important for validating site policy semantics

---

### 4. JACI / Cray-like environment

**Status:** validated in real environment, but still partially heuristic by class

**Scope:** supported with care

Typical characteristics:

- wrapper-driven toolchain behavior
- Cray-like compiler exposure
- possible environment complexity around `cc`, `CC`, `ftn`, `PrgEnv-*`

Expected use:

- detection and policy derivation for Cray-like environments
- layered site generation

Notes:

- this environment class remains more heuristic than ordinary Linux cluster support
- maintainers should inspect reports and outputs carefully

---

## Package support

### Supported package set

The current supported package focus is:

- `openmpi`
- `mpich`
- `hdf5`
- `netcdf-c`
- `netcdf-fortran`

These packages are part of the intended public support surface for the current line.

### Current support intent

- MPI implementations are central to provider policy
- HDF5 and NetCDF are central to the current scientific stack use cases
- the project is not trying to be a general detector for the whole Spack ecosystem yet

---

## Feature support matrix

### External package detection

**Status:** supported

Coverage focus:

- MPI
- HDF5
- NetCDF-C
- NetCDF-Fortran

### Validation

**Status:** supported

Coverage focus:

- wrapper inspection
- config tool inspection
- optional compile checks
- linkage inspection

### Unified `packages.yaml`

**Status:** supported

### Layered site generation

**Status:** supported

Generated outputs:

- `configs/common/*`
- `configs/sites/<site>/*`
- `configs/templates/<template>/spack.yaml`

### Facts / policy / authority / trace separation

**Status:** supported

### Platform facts and policy distinction

**Status:** supported

Important scope:

- detected `operating_system`
- detected `target`
- policy-level overrides
- renderer consumption of final policy values

### Configurable external promotion mode

**Status:** supported

Supported values:

- `all`
- `providers-only`

---

## What is intentionally not promised yet

The following are intentionally not claimed as broad stable support:

- arbitrary package detection beyond the focused supported set
- fully generic support for every HPC environment variation
- total elimination of heuristics in compiler/toolchain inference
- full replacement of upstream `spack-stack`
- site-independent behavior without report inspection in complex HPC environments

---

## Practical interpretation for 1.0.0

For the `1.0.0` line, the intended meaning should be:

- the documented supported environment classes are real targets
- the documented package set is the real supported package scope
- the documented generated artifact set is the real output contract
- behavior outside that scope should not be described as guaranteed support

---

## Summary

`bootstrap-spack` is already strong enough to claim a real support surface, but that support surface should remain focused and explicit.

The safest 1.0.0 position is:

- support the environment classes that are already validated and understood
- support the package set the tool was actually built around
- be honest about heuristic areas instead of overstating generality
