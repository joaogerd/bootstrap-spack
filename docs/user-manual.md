# User Manual

## Purpose

`bootstrap-spack` is a bootstrap utility for machines where the software stack already exists and needs to be described cleanly for Spack or for a layered `spack-stack`-style site layout.

The main idea is simple:

1. load a controlled environment;
2. detect and validate external packages;
3. derive a site policy from detected facts plus configuration;
4. write inspectable YAML artifacts.

This is especially useful when you do not want to hand-maintain `packages.yaml`, `compilers.yaml` and the surrounding site files for each machine.

---

## What the tool generates

A typical execution can generate two groups of outputs.

### Unified outputs

These are written directly in the output directory:

- `packages.yaml`
- `detection-report.txt`

These are useful for direct Spack use and for diagnosis.

### Layered outputs

When `site.name` is enabled, the tool also writes:

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

These files are intended for a site-oriented workflow closer to `spack-stack`.

---

## Installation

Install the package in editable mode:

```bash
pip install -e .
```

For development:

```bash
pip install -e .[dev]
```

The current release line uses:

- `pyyaml`
- `archspec`
- `distro`

---

## First execution

Run:

```bash
bootstrap --config env/egeon.yaml --output-dir out --debug
```

Typical result:

```text
out/
  packages.yaml
  detection-report.txt
  configs/
    common/
    sites/
    templates/
```

The `--debug` flag is useful when you want to see which modules were loaded, which fallback modules were tried, and which specs were reconstructed.

---

## Configuration structure

A configuration file is organized around these sections:

- `platform`
- `modules`
- `packages`
- `validation`
- `site`
- `template`
- `output`

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

### Site-oriented example

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

---

## Understanding platform facts

One of the most important points in the 0.4.1 line is the separation between:

- detected host facts;
- final site policy.

### Detected facts

These represent the real machine.

Examples:

- detected operating system: `rhel8`
- detected target: `zen2`

### Final policy

These are the values used in rendered artifacts.

Examples:

- policy operating system: `rhel8`
- policy target: `core2`

This matters because an institutional choice such as `core2` should not be confused with the physical host fact `zen2`.

---

## Platform overrides

You can explicitly override platform policy values when needed.

Example:

```yaml
site:
  policy_overrides:
    platform:
      operating_system: rhel8
      target: core2
```

Use this when the generated site should intentionally target something more conservative than the detected host.

---

## Runtime overrides

Runtime-related site values can also be overridden.

Example:

```yaml
site:
  policy_overrides:
    runtime:
      build_jobs: 16
      install_tree_root: /scratch/site/spack/opt
      build_stage:
        - /scratch/site/spack/stage
      test_stage: /scratch/site/spack/test
      source_cache: /scratch/site/spack/cache/source
      misc_cache: /scratch/site/spack/cache/misc
```

These values are recorded in the derived policy and in the report authority/trace sections.

---

## MPI provider overrides

MPI provider policy can be overridden explicitly.

Example:

```yaml
site:
  policy_overrides:
    providers:
      mpi:
        - openmpi
```

This is useful when you need the generated site policy to force a specific provider choice.

---

## External promotion modes

The site `packages.yaml` supports two promotion behaviors.

### Mode 1: `all`

```yaml
site:
  external_promotion_mode: all
```

This promotes all validated requested externals into:

```text
configs/sites/<site>/packages.yaml
```

Typical effect:

- `openmpi` externalized
- `hdf5` externalized
- `netcdf-c` externalized
- `netcdf-fortran` externalized

This is the more permissive mode and is useful when you want the site YAML to reflect the full detected host stack.

### Mode 2: `providers-only`

```yaml
site:
  external_promotion_mode: providers-only
```

This promotes only packages selected as site providers, especially MPI.

Typical effect:

- `openmpi` externalized
- `hdf5` left `buildable: true`
- `netcdf-c` left `buildable: true`
- `netcdf-fortran` left `buildable: true`

This is useful when you want a more conservative site policy for `spack-stack` concretization.

### Practical interpretation

- choose `all` when you want a site file that mirrors the detected stack more aggressively;
- choose `providers-only` when you want to keep the site file lighter and let Spack build more of the dependency graph.

---

## Reading the generated files

### `packages.yaml` in the output root

This is the unified output for direct Spack use.

It typically includes all detected validated packages plus provider hints.

### `configs/common/packages.yaml`

This stores shared provider policy, such as:

- MPI provider selection

### `configs/sites/<site>/packages.yaml`

This stores site-specific promoted externals according to `external_promotion_mode`.

### `configs/sites/<site>/compilers.yaml`

This stores the detected compiler entry, but rendered with final policy values for:

- `operating_system`
- `target`

This is important because the final site compiler YAML should reflect policy, not only raw compiler metadata.

### `configs/sites/<site>/config.yaml`

This stores runtime-oriented site values such as:

- build jobs
- install tree root
- build stage
- test stage
- source cache
- misc cache

### `configs/templates/<template>/spack.yaml`

This stores the template environment intent.

Example:

```yaml
spack:
  specs:
    - mpas-bundle %gcc
```

---

## Detection report

The report is written to:

```text
<output-dir>/detection-report.txt
```

This file is useful to understand:

- which packages were detected;
- why validation passed or failed;
- which specs were generated;
- which facts were detected;
- which policy values were chosen;
- which overrides were applied;
- which authority produced each important decision.

When diagnosing a problem, this file should be the first thing to inspect.

---

## Typical workflow for a new machine

A practical workflow is:

1. prepare a configuration file for the machine;
2. define the base modules that represent the intended compiler/MPI environment;
3. run `bootstrap --config ... --output-dir ... --debug`;
4. inspect `detection-report.txt`;
5. inspect `configs/sites/<site>/compilers.yaml`;
6. inspect `configs/sites/<site>/packages.yaml`;
7. adjust overrides only when the policy should intentionally differ from detection.

A good rule is:

- keep detected facts honest;
- apply overrides only for real institutional reasons.

---

## Example: EGEON-style conservative site output

If you want a conservative site file where only MPI is externalized:

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

Expected site `packages.yaml` shape:

```yaml
packages:
  openmpi:
    externals:
      - spec: openmpi@4.1.1
        prefix: /opt/ohpc/pub/mpi/openmpi4-gnu9/4.1.1
    buildable: false
  hdf5:
    buildable: true
  netcdf-c:
    buildable: true
  netcdf-fortran:
    buildable: true
```

---

## Example: full external promotion

If instead you want the site file to carry all validated externals:

```yaml
site:
  external_promotion_mode: all
```

This is the right option when you want a fuller site representation of the host stack.

---

## Testing

Run the automated test suite with:

```bash
pytest
```

For development checks:

```bash
ruff check .
mypy bootstrap
```

---

## Practical advice

A few practical rules help a lot.

- Do not confuse detected host facts with institutional policy.
- Prefer no override unless there is a real reason.
- Use `providers-only` when a conservative site `packages.yaml` helps concretization.
- Use `all` when you want the generated site file to reflect the validated host stack more completely.
- Always inspect `detection-report.txt` after running on a new machine.

---

## Summary

`bootstrap-spack` is most useful when you need a bridge between a real preinstalled HPC environment and a clean, inspectable Spack or `spack-stack` description.

The 0.4.1 line is especially about making that bridge more honest and more controllable by separating:

- detected facts
- derived policy
- rendered artifacts
