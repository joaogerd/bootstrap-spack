# How to Add a New Machine

## Purpose

This guide describes a practical workflow for onboarding a new machine into `bootstrap-spack`.

The main idea is simple:

1. start from the real machine;
2. define a clean bootstrap configuration;
3. run detection in a controlled environment;
4. inspect facts, policy and rendered artifacts;
5. apply overrides only when there is a real institutional reason.

---

## Step 1 — Identify the target environment

Before writing any configuration, answer these questions.

### Machine profile

- Is this a generic Linux machine?
- Is this a cluster with Lmod or Environment Modules?
- Is this a Cray-like environment?
- Is there a site-specific institutional convention already in place?

### Software stack

- Which compiler toolchain should represent the site?
- Which MPI implementation should represent the site?
- Are HDF5 and NetCDF expected to be treated as externals or allowed to remain buildable?

### Operational intent

- Do you want the generated site files to mirror the host stack aggressively?
- Or do you want a conservative `spack-stack` site policy?

That last question is what usually determines the choice of `external_promotion_mode`.

---

## Step 2 — Prepare a first configuration file

Start with the smallest honest configuration that represents the intended environment.

Example:

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
  name: mysite
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

At this stage, keep overrides out unless you already know you need them.

---

## Step 3 — Choose the external promotion mode

You now have two explicit choices.

### Option A — `all`

```yaml
site:
  external_promotion_mode: all
```

Use this when you want the site `packages.yaml` to reflect the validated host stack more fully.

Typical effect:

- MPI externalized
- HDF5 externalized
- NetCDF externalized

### Option B — `providers-only`

```yaml
site:
  external_promotion_mode: providers-only
```

Use this when you want a conservative site file.

Typical effect:

- MPI externalized
- HDF5 buildable
- NetCDF buildable

This is often the better starting point for `spack-stack`-style site policy.

---

## Step 4 — Run the bootstrap

Run:

```bash
bootstrap --config env/mysite.yaml --output-dir out --debug
```

The `--debug` flag is strongly recommended when onboarding a machine.

It helps you see:

- loaded base modules
- attempted fallback modules
- reconstructed package specs
- basic toolchain results

---

## Step 5 — Inspect the detection report first

Always inspect:

```text
out/detection-report.txt
```

This is the main operational document for understanding what happened.

Look for:

- detected packages
- validation status
- generated specs
- detected platform facts
- derived policy
- policy authority
- policy decision trace
- warnings

Do not start by editing YAML outputs. Start by understanding the report.

---

## Step 6 — Inspect the layered outputs

Then inspect the generated site files.

### `configs/sites/<site>/compilers.yaml`

Check that:

- `spec` is correct
- `operating_system` is normalized correctly
- `target` reflects the intended site policy

This file should reflect final policy values, not accidental compiler metadata residue.

### `configs/sites/<site>/packages.yaml`

Check that promotion behavior matches your intent.

Ask:

- do I want all validated externals here?
- or do I want only providers such as MPI here?

### `configs/sites/<site>/config.yaml`

Check:

- build jobs
- install tree root
- build stage
- cache paths

### `configs/templates/<template>/spack.yaml`

Check that the template specs match the intended environment definition.

---

## Step 7 — Apply overrides only if needed

Overrides should not be your first move.

They should only be used when the final site policy must intentionally differ from the detected facts.

Typical cases:

- institutional target must be `core2` even though the host is `zen2`
- runtime paths must point to site-owned storage locations
- MPI provider policy must be forced explicitly

Example:

```yaml
site:
  policy_overrides:
    platform:
      target: core2
    runtime:
      build_jobs: 16
      install_tree_root: /scratch/site/spack/opt
    providers:
      mpi:
        - openmpi
```

---

## Step 8 — Re-run and compare

After changing configuration or overrides, run the bootstrap again and compare:

- previous report vs new report
- previous `compilers.yaml` vs new `compilers.yaml`
- previous `packages.yaml` vs new `packages.yaml`

The important question is not only “did it run?”
The important question is “does the new policy now match the intended site semantics?”

---

## Step 9 — Validate in the real target workflow

Before declaring the machine onboarded, validate the generated files in the real workflow they are meant to support.

Examples:

- direct Spack usage with generated `packages.yaml`
- layered `spack-stack` site usage
- environment concretization in the target application stack

A machine is not truly onboarded only because the bootstrap succeeded.
It is onboarded when the generated files are operationally usable.

---

## Practical advice

A few rules help a lot.

- Keep detected facts honest.
- Do not use overrides to hide misunderstandings.
- Start conservative when unsure.
- Use `providers-only` first if concretization compatibility matters.
- Use `all` when you intentionally want the generated site file to mirror the detected stack more fully.
- Treat `detection-report.txt` as the main diagnostic artifact.

---

## Minimal onboarding checklist

- [ ] Configuration file created
- [ ] Base modules selected
- [ ] Bootstrap executed with `--debug`
- [ ] Detection report reviewed
- [ ] `compilers.yaml` reviewed
- [ ] `packages.yaml` reviewed
- [ ] Runtime `config.yaml` reviewed
- [ ] Template `spack.yaml` reviewed
- [ ] Overrides applied only where justified
- [ ] Real target workflow validated

---

## Summary

Onboarding a new machine should follow this logic:

- detect honestly
- derive policy carefully
- override deliberately
- validate operationally

That sequence keeps `bootstrap-spack` useful as a real institutional tool instead of turning it into a collection of ad hoc YAML patches.
