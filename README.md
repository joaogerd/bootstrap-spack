<p align="center">
  <img src="docs/assets/logo.png" alt="bootstrap-spack logo" width="480">
</p>

<p align="center">
  Detect external HPC software stacks and generate practical Spack and spack-stack configuration artifacts.
</p>

---

## Overview

`bootstrap-spack` is a Python utility for environments where scientific software is already installed on the machine and needs to be described cleanly for Spack or for a layered `spack-stack`-style site layout.

The project is built around a practical HPC problem:

- MPI, HDF5 and NetCDF are often already available on the system;
- wrappers, compiler paths and module names differ from machine to machine;
- the values that describe the host are not always the same values that should become institutional site policy;
- maintainers need repeatable outputs instead of hand-written YAML files.

Instead of manually building those files, `bootstrap-spack` inspects the host environment, validates candidate tools, reconstructs external package information, derives a site policy and writes inspectable YAML artifacts.

---

## Release status

The current release line is **0.4.1**.

This release closes an important platform-policy bugfix cycle on top of the 0.4.0 policy-engineering architecture.

The 0.4.1 line adds three central improvements:

- explicit platform facts for detected `platform`, `operating_system` and `target`;
- policy derivation that separates detected host facts from final site policy;
- configurable site external promotion behavior for layered `packages.yaml` generation.

In practical terms, the project now distinguishes clearly between:

- what was detected from the real machine;
- what was selected as final policy for the generated site;
- what was rendered into final YAML artifacts.

This matters especially for fields such as:

- `operating_system`
- `target`
- package external promotion into `configs/sites/<site>/packages.yaml`

---

## What the project does

The current implementation provides five main capabilities.

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

### 3. Explicit platform fact detection

The project now detects platform facts independently from compiler metadata.

This includes:

- normalized platform name
- normalized operating system
- detected host target architecture

Examples:

- `rhel 8.4` → `rhel8`
- `rocky 8.9` → `rocky8`
- `ubuntu 22.04` → `ubuntu22.04`
- `x86_64` host family resolved through `archspec` to targets such as `zen2`

### 4. Unified Spack output generation

The project generates a unified `packages.yaml` suitable for direct Spack use, including:

- detected externals
- `buildable: false` for validated host packages
- provider hints such as MPI when applicable

It also writes a human-readable detection report for debugging and auditing.

### 5. Layered spack-stack-style site generation

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

This allows the project to represent:

- shared policy in `common`
- machine-specific site policy in `sites/<site>`
- environment intent in `templates/<template>`

---

## Installation

```bash
pip install -e .
```

For development tooling:

```bash
pip install -e .[dev]
```

The 0.4.1 line depends on:

- `pyyaml`
- `archspec`
- `distro`

---

## Quick start

### Generate outputs using a site config

```bash
bootstrap --config env/egeon.yaml --output-dir out --debug
```

This writes at least:

```text
out/
  packages.yaml
  detection-report.txt
```

and, when `site` is enabled, also writes the layered tree under `out/configs/`.

### Run the test suite

```bash
pytest
```

---

## Configuration model

The bootstrap configuration is YAML-based.

At a high level, the current model is organized around these sections:

- `platform`: requested platform profile such as `linux`, `cluster` or `cray`
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
platform: cluster

modules:
  load:
    - gnu9/9.4.0
    - openmpi4/4.1.1
  optional: []

packages:
  external:
    - openmpi
    - hdf5
    - netcdf-c
    - netcdf-fortran

validation:
  strict: true

site:
  name: egeon
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  external_promotion_mode: providers-only
  core_compilers:
    - gcc@9.4.0

template:
  name: mpas-bundle
  specs:
    - mpas-bundle
  compiler: gcc

output:
  directory: .
```

### Example with controlled policy overrides

```yaml
site:
  name: egeon
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  external_promotion_mode: providers-only
  core_compilers:
    - gcc@9.4.0
  policy_overrides:
    providers:
      mpi:
        - openmpi
    platform:
      target: core2
    runtime:
      build_jobs: 16
      install_tree_root: /scratch/site/spack/opt
      build_stage:
        - /scratch/site/spack/stage
      test_stage: /scratch/site/spack/test
      source_cache: /scratch/site/spack/cache/source
      misc_cache: /scratch/site/spack/cache/misc
```

These overrides are not applied silently. They become part of the derived policy, are marked as explicit authority in the report, and are traced as override decisions.

---

## External promotion modes

The layered site `packages.yaml` now supports an explicit promotion policy through:

```yaml
site:
  external_promotion_mode: all
```

or:

```yaml
site:
  external_promotion_mode: providers-only
```

### `all`

Promotes all validated requested externals into `configs/sites/<site>/packages.yaml`.

This is the more permissive and more traditional behavior.

### `providers-only`

Promotes only packages selected as important site providers, such as MPI.

This is useful when you want a more conservative `spack-stack` site policy and prefer packages like HDF5 or NetCDF to remain buildable unless explicitly pinned later.

---

## Platform facts and policy semantics

The 0.4.1 line fixes an important architectural ambiguity.

The project now treats these as different things:

### Detected platform facts

Examples:

- detected OS: `rhel8`
- detected target: `zen2`

These are facts about the host.

### Final site policy

Examples:

- policy OS: `rhel8`
- policy target: `core2`

These are the values that may be rendered into final site artifacts.

This means an institutional target such as `core2` is no longer confused with a detected hardware fact.

---

## Outputs

### Unified outputs

#### `packages.yaml`

Generated for direct Spack use.

Typical content includes:

- external package specs
- external prefixes
- buildability policy
- common provider hints when applicable

#### `detection-report.txt`

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
- precedence metadata for authority records

### Layered outputs

When `site.name` is configured, the project additionally generates:

#### `configs/common/packages.yaml`

Shared package policy such as provider hints.

#### `configs/common/modules.yaml`

Shared module policy such as enabled module backend.

#### `configs/sites/<site>/packages.yaml`

Site-specific external package declarations according to `external_promotion_mode`.

#### `configs/sites/<site>/compilers.yaml`

Compiler entry rendered using final policy `operating_system` and `target` values.

#### `configs/sites/<site>/modules.yaml`

Site-specific module settings such as `core_compilers`.

#### `configs/sites/<site>/config.yaml`

Runtime-oriented configuration derived from host detection and policy overrides.

#### `configs/templates/<template>/spack.yaml`

A minimal template environment definition using the configured specs and optional compiler projection.

---

## Internal architecture model

The internal model is organized around six semantic layers.

### 1. Requested configuration

`BootstrapConfig` represents what the user asked for.

### 2. Detected host facts

`DetectedHostFacts` represents what the host actually exposed, including:

- platform family
- explicit platform facts
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
- final platform policy values

### 4. Policy authority

`PolicyAuthority` represents the authority that produced an important policy value.

### 5. Policy decision trace

`PolicyDecisionTrace` records why the policy looks the way it does.

### 6. Rendered artifacts

`LayeredSpackStackArtifacts` represents the materialized YAML outputs.

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
- platform facts are modeled explicitly instead of being inferred only from compiler metadata
- override is treated as a formal authority layer rather than a silent mutation
- renderers are split by output artifact
- the project favors inspectable YAML outputs over hidden implicit behavior
- real-machine validation is treated as first-class feedback for the implementation

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

## Documentation

A more practical usage manual is available at:

- `docs/user-manual.md`

---

## Development notes

Typical development workflow:

```bash
ruff check .
pytest
mypy bootstrap
```

---

## License

MIT
