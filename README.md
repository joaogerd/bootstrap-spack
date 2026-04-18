<p align="center">
  <img src="docs/assets/logo.png" alt="bootstrap-spack logo" width="180">
</p>

<h1 align="center">bootstrap-spack</h1>

<p align="center">
  Detect external HPC software stacks and generate practical Spack and spack-stack configuration artifacts.
</p>

---

## Overview

`bootstrap-spack` is a Python-based bootstrap utility for environments where scientific software is already available on the system and needs to be described cleanly for Spack.

The project focuses on a common HPC problem:

- external MPI, HDF5 and NetCDF installations already exist;
- compiler and MPI wrappers differ across machines;
- module systems behave differently on Linux, HPE and Cray-like platforms;
- site maintainers need a repeatable way to generate `packages.yaml`, diagnostics and layered site configuration.

Instead of manually writing everything by hand, `bootstrap-spack` inspects the host environment, validates candidate tools, reconstructs external package information, checks basic toolchain consistency and writes configuration outputs that can be reused in Spack or a spack-stack-style layout.

---

## What the project does

The current implementation provides four main capabilities.

### 1. External package detection

The tool detects selected external packages from the current environment and optional module context, with support centered on:

- MPI implementations such as Open MPI and MPICH
- HDF5
- NetCDF-C
- NetCDF-Fortran

Detection is based on real tools and wrappers such as `mpicc`, `h5cc`, `nc-config` and `nf-config`.

### 2. Validation and consistency checks

Detection is not based only on `PATH` lookup.

The tool can validate packages using:

- wrapper inspection
- configuration tools
- optional compile tests in strict mode
- dynamic linkage inspection via `ldd`
- basic consistency checks across MPI / HDF5 / NetCDF relationships

### 3. Spack output generation

The project generates a unified `packages.yaml` suitable for direct Spack use, including:

- detected externals
- `buildable: false` for validated host packages
- provider hints such as MPI when applicable

It also writes a human-readable detection report for debugging and auditing.

### 4. Layered spack-stack-style site generation

When site and template configuration are enabled, the tool generates a layered tree inspired by the `spack-stack` model:

```text
<output-dir>/
  configs/
    common/
      packages.yaml
      modules.yaml
    sites/
      <site>/
        packages.yaml
        compilers.yaml
        modules.yaml
        config.yaml
    templates/
      <template>/
        spack.yaml
```

This lets the project represent:

- shared policy in `common`
- machine-specific facts and settings in `sites/<site>`
- environment intent in `templates/<template>`

---

## Supported environment profiles

The project has been shaped around practical execution on:

- generic Linux workstations and laptops
- cluster environments using Lmod or Environment Modules
- Cray-like environments using `PrgEnv-*`, `cc`, `CC`, `ftn`
- HPE / HPC environments that expose wrapper-based compiler and MPI toolchains

Support is pragmatic and environment-driven. Some parts of the project are still heuristic by nature, especially compiler and toolchain inference.

---

## Installation

```bash
pip install -e .
```

For development tooling:

```bash
pip install -e .[dev]
```

---

## Quick start

### Generate a unified `packages.yaml`

```bash
bootstrap --config env/egeon.yaml --output-dir out --debug
```

This writes, at minimum:

```text
out/
  packages.yaml
  detection-report.txt
```

### Generate layered spack-stack-style outputs

```bash
bootstrap --config env/linux_spack_stack_site.yaml --output-dir out --debug
```

This writes the unified outputs and, when `site` is enabled, the layered site tree as well.

---

## Configuration model

The bootstrap configuration is YAML-based.

At a high level, the current model is organized around these sections:

- `platform`: target platform profile such as `linux` or `cray`
- `modules`: base and optional modules to use during detection
- `packages`: requested external packages to inspect
- `validation`: strict or non-strict validation mode
- `site`: site generation settings for layered output
- `template`: optional environment template for `spack.yaml`
- `output`: output directory

### Minimal example

```yaml
platform: linux

modules:
  load: []
  optional: []

packages:
  external:
    - openmpi
    - hdf5
    - netcdf-c
    - netcdf-fortran

validation:
  strict: false

output:
  directory: .
```

### Example with layered site generation

```yaml
platform: cray

modules:
  load:
    - PrgEnv-gnu
    - cray-mpich
  optional:
    - cray-netcdf
    - cray-hdf5

packages:
  external:
    - mpich
    - hdf5
    - netcdf-c
    - netcdf-fortran

validation:
  strict: true

site:
  name: jaci
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  core_compilers:
    - gcc

template:
  name: mpas-bundle
  specs:
    - mpas-bundle
  compiler: gcc

output:
  directory: .
```

---

## Outputs

## Unified outputs

### `packages.yaml`

Generated for direct Spack use.

Typical content includes:

- external package specs
- external prefixes
- buildability policy
- common provider hints when applicable

### `detection-report.txt`

A human-readable report with:

- package detection status
- validation reasons
- linkage information
- generated specs
- toolchain consistency summary

## Layered outputs

When `site.name` is configured, the project additionally generates:

### `configs/common/packages.yaml`

Shared package policy such as provider hints.

### `configs/common/modules.yaml`

Shared module policy such as enabled module backend.

### `configs/sites/<site>/packages.yaml`

Site-specific external package declarations.

### `configs/sites/<site>/compilers.yaml`

Detected compiler entry for the host environment.

### `configs/sites/<site>/modules.yaml`

Site-specific module settings such as `core_compilers`.

### `configs/sites/<site>/config.yaml`

Runtime-oriented configuration derived from host detection, such as:

- build jobs
- install tree root
- build stage
- test stage
- source cache
- misc cache

### `configs/templates/<template>/spack.yaml`

A minimal template environment definition using the configured specs and optional compiler projection.

---

## Design principles

The project is organized around a layered internal architecture:

- `domain` → explicit models and semantic structures
- `application` → orchestration use cases
- `infrastructure` → shell execution, module handling, validation, rendering and detection
- `services` → high-level bootstrap flow
- `interfaces` → CLI and presentation

Some design choices are deliberate:

- detected facts and generated policy are kept separate as much as possible
- platform-specific behavior is handled pragmatically rather than abstractly over-generalized
- renderers are split by output artifact
- the project favors inspectable YAML outputs over hidden implicit behavior

---

## Current strengths

The current implementation is strongest in these areas:

- practical detection of external HPC libraries
- wrapper-aware validation
- Linux and Cray-like compiler detection paths
- layered spack-stack-style output generation
- transparent YAML artifacts that can be inspected and versioned
- unit test coverage for the bootstrap core and renderer layer

---

## Current limitations

This project is already useful, but it is still evolving.

Important current limitations include:

- compiler and toolchain inference still rely partly on heuristics
- support is centered on a focused package set, not the full Spack ecosystem
- layered output is a practical base for spack-stack-style layouts, not a complete replacement for the full upstream spack-stack project
- some generated policy is still derived automatically from detected host facts, which may need manual refinement in institutional environments
- module system behavior can remain site-specific and sometimes surprising on real HPC machines

---

## Testing

Run the test suite with:

```bash
pytest
```

The project includes focused unit tests for:

- spec generation
- toolchain checks
- patching of typed validation details
- package registry behavior
- package detection flow
- YAML renderers
- site tree generation
- command runner behavior
- configuration loading for layered site/template flows

---

## Development notes

Typical development workflow:

```bash
ruff check .
pytest
mypy bootstrap
```

---

## Roadmap direction

The current direction of the project points toward:

- stronger separation between detected host facts and generated site policy
- richer layered `common / site / template` generation
- more explicit platform profiles
- more robust compiler and runtime modeling for heterogeneous HPC systems
- broader package support and additional validation backends
- stronger integration-style tests for real bootstrap flows

---

## License

MIT
