# Investigation Plan — Real `spack-stack` Compatibility

## Purpose

This document records the main technical conclusion from the recent manual validation work against the real `spack-stack` workflow.

The central point is this:

> It is not enough for `bootstrap-spack` to generate files that are syntactically valid for Spack.
> The generated site must be compatible with the real operational workflow used by `spack-stack`, including meta-module generation.

This document turns that conclusion into a concrete investigation and development plan for the path to `1.0.0`.

---

## Executive summary

Manual testing on EGEON showed that the current generated site is already strong enough to:

- create the environment
- load the generated site data
- integrate `site`, `common` and `template`
- support concretization and installation-oriented setup steps

However, the full target workflow exposed a critical remaining gap:

```text
spack stack setup-meta-modules
==> Error: No matching compilers found
```

This means the current `bootstrap-spack` output is still insufficient for the complete real `spack-stack` lifecycle.

The issue is not merely environment creation.
The issue is compatibility with the full JCSDA-style site behavior.

---

## Consolidated architectural understanding

The project is now conceptually organized around three layers.

### 1. Site

Represents the machine-specific layer:

- compiler policy
- MPI policy
- modules
- target
- operating system
- runtime paths
- local policy decisions

This is the part that should come from `bootstrap-spack`.

### 2. Template

Represents the machine-independent application environment:

- which packages compose the target environment
- environment intent independent of site-specific hardware details

This is the part that should remain generic.

### 3. Materialization / automation

Combines:

- `site`
- `template`
- `common`
- the scripts that create and manage real environments

This is the operational layer around the generated artifacts.

---

## Key discovery from manual testing

The environment creation path itself is not the main problem.

The generated site already proved sufficient for:

- `spack stack create env`
- site and common inclusion
- template inclusion
- reading the generated `compilers.yaml`
- reading the generated `packages.yaml`
- reading the generated `modules.yaml`
- reading the generated `config.yaml`

The most important failure was later in the real workflow:

```text
spack stack setup-meta-modules
==> Error: No matching compilers found
```

This reveals that:

- the site is structurally integrated;
- the remaining gap is semantic compatibility with the meta-module phase.

---

## What this changes in the project goal

The project goal must now be stated more precisely.

The target is not:

- “generate minimal valid Spack YAML files”

The target is:

- “generate a site compatible with the real `spack-stack` workflow”

That workflow must be understood as including at least:

- `spack stack create env`
- `spack concretize`
- `spack install`
- `spack module lmod refresh`
- `spack stack setup-meta-modules`

If the generated site fails in that sequence, the product contract is still incomplete.

---

## Current strongest hypothesis

One strong technical hypothesis emerged from the manual analysis:

- `compilers.yaml` alone is not enough for the `setup-meta-modules` phase;
- the compiler may also need to be represented in `packages.yaml` in a way that `spack-stack` expects.

This should still be treated as a **strong hypothesis**, not as a proven final conclusion.

Possible needs include:

- compiler represented as an external package in `packages.yaml`
- `mpi: buildable: false`
- compiler metadata under `extra_attributes.compilers`
- additional details expected by the `spack-stack` meta-module logic

This investigation must remain evidence-driven.

---

## Example of the currently insufficient site `packages.yaml`

The current minimal generated site-level shape can look like this:

```yaml
packages:
  openmpi:
    externals:
      - spec: openmpi@4.1.1
        prefix: /opt/ohpc/pub/mpi/openmpi4-gnu9/4.1.1
    buildable: false
```

This is useful, but it may be insufficient for the full `spack-stack` lifecycle.

A more compatible shape may need to look closer to something like:

```yaml
packages:
  gcc:
    externals:
      - spec: gcc@9.4.0 languages='c,c++,fortran'
        prefix: /opt/ohpc/pub/compiler/gcc/9.4.0
        extra_attributes:
          compilers:
            c: /opt/ohpc/pub/compiler/gcc/9.4.0/bin/gcc
            cxx: /opt/ohpc/pub/compiler/gcc/9.4.0/bin/g++
            fortran: /opt/ohpc/pub/compiler/gcc/9.4.0/bin/gfortran

  mpi:
    buildable: false

  openmpi:
    externals:
      - spec: openmpi@4.1.1
        prefix: /opt/ohpc/pub/mpi/openmpi4-gnu9/4.1.1
    buildable: false
```

This is not yet asserted as final truth.
It is the current leading investigation direction.

---

## Important additional observation about modules

The manual EGEON test also suggested an important point about module semantics.

The effective `modules.yaml` behavior was coherent because the broader `spack-stack` model already brings conventions such as:

- a dummy or baseline `core_compilers` concept
- later generation of `stack-gcc/...`
- later generation of `stack-openmpi/...`

This suggests that `bootstrap-spack` should not try to naively collapse the entire module policy into the immediate physical compiler identity.

That area needs careful compatibility-driven interpretation.

---

## Development consequence

The investigation implies a new explicit requirement for the path to `1.0.0`:

> `bootstrap-spack` must be validated not only against isolated generated files, but against the real operational behavior of `spack-stack`.

This becomes a product-level requirement.

---

## Concrete investigation tasks

### 1. Compare generated site with a known-good `spack-stack` site

- [ ] collect a reference site layout that works cleanly with `setup-meta-modules`
- [ ] compare `packages.yaml`
- [ ] compare `compilers.yaml`
- [ ] compare `modules.yaml`
- [ ] compare any compiler-related metadata expected by `spack-stack`

### 2. Investigate compiler representation in `packages.yaml`

- [ ] determine whether compiler-as-external is required
- [ ] determine required spec form
- [ ] determine whether `languages='c,c++,fortran'` or equivalent is needed
- [ ] determine whether `extra_attributes.compilers` is required

### 3. Investigate MPI package semantics for meta-modules

- [ ] determine whether `mpi: buildable: false` is required
- [ ] determine whether additional provider declarations are required beyond current behavior
- [ ] verify whether current `openmpi` externalization is sufficient or incomplete

### 4. Investigate module and core compiler expectations

- [ ] understand what `setup-meta-modules` expects for compiler matching
- [ ] verify interaction between generated `core_compilers` and meta-module generation
- [ ] verify whether current `modules.yaml` generation should evolve to better follow JCSDA conventions

### 5. Build reproducible regression tests

- [ ] create fixture-based test cases reflecting the compatibility findings
- [ ] create regression tests for compiler representation if added to `packages.yaml`
- [ ] create regression tests for provider/meta-module-related site policy behavior

---

## 1.0.0 implication

This investigation is not an optional refinement.
It is part of what determines whether `1.0.0` is truly ready for production-oriented use.

If `bootstrap-spack` still fails on the real `spack-stack` lifecycle, then:

- the generated site contract is still incomplete;
- the project is not yet fully production-ready.

---

## Practical decision rule

The project should treat this as a release gate question:

> Can the generated site be used successfully through the real target workflow, including meta-modules?

If the answer is not yet yes, this remains a `pre-1.0.0` task.

---

## Summary

The manual analysis showed that the current project is already strong in:

- site generation
- facts/policy separation
- platform-policy handling
- layered outputs

But it also exposed a critical remaining gap:

- compatibility with the full operational `spack-stack` behavior

That gap must now be treated as a first-class investigation line in the development toward `1.0.0` and then real production use.
