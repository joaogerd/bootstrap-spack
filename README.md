<p align="center">
  <img src="docs/assets/logo.png" alt="bootstrap-spack logo" width="480">
</p>

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

## Release status

The current release line is **0.4.0**.

This release builds on the 0.3.0 architectural split and moves the project into its first **policy engineering** phase.

The tool now operates around explicit internal layers for:

- detected host facts;
- derived site policy;
- policy authority;
- policy decision trace;
- layered artifact generation.

In practical terms, the project now distinguishes more clearly between:

- what was observed on the host;
- what was inferred as site policy;
- which authority produced each important policy value;
- why those policy decisions were taken;
- what was rendered as final configuration files.

The policy trace is no longer only a flat list of messages. It now supports structured trace entries that capture:

- decision message;
- source of the decision;
- rationale;
- confidence level;
- fallback used, when applicable.

The derived policy model also carries explicit authority metadata for key decisions such as:

- module backend selection;
- compiler policy;
- runtime policy;
- MPI provider policy;
- common module policy;
- template enablement.

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

## Internal architecture model

The internal model is now organized around six semantic layers.

### 1. Requested configuration

`BootstrapConfig` represents what the user asked for.

### 2. Detected host facts

`DetectedHostFacts` represents what the host actually exposed, including:

- platform family
- loaded modules
- optional module candidates
- detected compiler entry
- validated packages
- linkage evidence
- detected runtime configuration

### 3. Derived site policy

`DerivedSitePolicy` represents the policy derived from configuration plus host facts, including:

- requested packages
- selected virtual providers
- compiler policy
- runtime policy
- common module policy
- template intent

### 4. Policy authority

`PolicyAuthority` represents the authority that produced an important policy value.

Each authority record captures:

- `key`
- `value`
- `source`
- `rationale`
- `confidence`
- `fallback_used`
- `overridden_by`
- `legacy_compat_used`

This is the semantic layer that allows the tool to distinguish between values that came from configuration, detection, derived policy, explicit override, default behavior or legacy compatibility.

### 5. Policy decision trace

`PolicyDecisionTrace` records why the policy looks the way it does.

The trace now contains:

- decision messages
- warnings
- assumptions
- structured trace entries

Each structured trace entry captures:

- `message`
- `source`
- `rationale`
- `confidence`
- `fallback_used`

### 6. Rendered artifacts

`LayeredSpackStackArtifacts` represents the materialized YAML outputs used to populate:

- `common`
- `site`
- `template`

This separation is important because it allows the tool to state more clearly what was detected automatically versus what was promoted to final site policy.

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
- detected host facts
- derived policy
- policy authority
- policy decision trace
- structured trace entries for policy decisions

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
- `application` → orchestration and policy derivation use cases
- `infrastructure` → shell execution, module handling, validation, rendering and detection
- `services` → high-level bootstrap flow
- `interfaces` → CLI and presentation

Some design choices are deliberate:

- detected facts and generated policy are kept separate as much as possible
- policy authority is modeled explicitly rather than left implicit in helper behavior
- platform-specific behavior is handled pragmatically rather than abstractly over-generalized
- renderers are split by output artifact
- the project favors inspectable YAML outputs over hidden implicit behavior
- real-machine validation is treated as first-class feedback for the implementation

---

## Current strengths

The current implementation is strongest in these areas:

- practical detection of external HPC libraries
- wrapper-aware validation
- Linux and Cray-like compiler detection paths
- layered spack-stack-style output generation
- transparent YAML artifacts that can be inspected and versioned
- unit test coverage for the bootstrap core and renderer layer
- explicit modeling of detected facts, derived policy and policy trace
- explicit modeling of authority for important policy decisions
- structured policy trace entries that make derivation decisions more auditable

---

## Current limitations

This project is already useful, but it is still evolving.

Important current limitations include:

- compiler and toolchain inference still rely partly on heuristics
- support is centered on a focused package set, not the full Spack ecosystem
- layered output is a practical base for spack-stack-style layouts, not a complete replacement for the full upstream spack-stack project
- some generated policy is still derived automatically from detected host facts, which may need manual refinement in institutional environments
- module system behavior can remain site-specific and sometimes surprising on real HPC machines
- provider selection and runtime policy remain pragmatic and are still being refined in the 0.4.x line
- override handling is now part of the semantic model, but broader controlled override flows are still being expanded

---

## Validation status

The current release line has been exercised in real environments including:

- EGEON
- JACI
- Linux local environment without modules

The automated test suite is also passing.

A practical way to interpret support maturity is:

- **validated in real environment** → exercised on an actual machine
- **validated by test suite** → covered by automated tests
- **heuristic** → supported by design but still dependent on environment-specific assumptions

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
- bootstrap service integration

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

- stronger policy engineering in `DerivedSitePolicy`
- richer and more explicit derivation rules
- richer authority modeling and controlled override handling
- more auditable decision traces with confidence and fallback reporting
- stronger distinction between detected host facts and final institutional policy
- more explicit platform profiles
- broader package support and additional validation backends
- stronger integration-style tests for real bootstrap flows

---

## License

MIT
