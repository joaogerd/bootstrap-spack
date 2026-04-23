# When to Use Overrides

## Purpose

Overrides are one of the most useful features of `bootstrap-spack`, but they are also one of the easiest ways to misuse the tool.

This guide explains when overrides are the right solution and when they are actually hiding a detection or configuration problem.

The core rule is simple:

- use overrides to express intentional institutional policy;
- do not use overrides to mask misunderstanding of the host environment.

---

## The key distinction

Before deciding whether to use an override, always distinguish between:

### Detected facts

These describe the real machine.

Examples:

- detected target is `zen2`
- detected operating system is `rhel8`
- detected compiler is `gcc@9.4.0`

### Final policy

These describe what the generated site should intentionally say.

Examples:

- final site target should be `core2`
- final runtime paths should point to institutional storage
- final MPI provider should be forced to `openmpi`

An override is correct only when the final policy should intentionally differ from the detected facts.

---

## Good reasons to use overrides

### 1. Conservative institutional target

Example:

- host fact: `zen2`
- site policy: `core2`

This is a valid override because the site wants a more conservative target than the physical host.

Configuration:

```yaml
site:
  policy_overrides:
    platform:
      target: core2
```

This is one of the best examples of an override that represents real policy rather than a workaround.

### 2. Institutional runtime paths

Example:

- detection suggests local defaults
- site requires scratch/cache/install locations under institutional directories

Configuration:

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

This is a good override because runtime layout is an institutional decision.

### 3. Forced MPI provider choice

Example:

- several MPI possibilities exist
- the site wants one provider as policy

Configuration:

```yaml
site:
  policy_overrides:
    providers:
      mpi:
        - openmpi
```

This is a valid override when the site already has a decided provider policy.

---

## Bad reasons to use overrides

### 1. The detection report was not read

If a package, compiler or target looks surprising, do not immediately override it.

First read:

- `detection-report.txt`
- detected facts
- policy authority
- policy trace

Many wrong overrides come from skipping diagnosis.

### 2. The module environment is wrong

If the wrong compiler or package was detected because the wrong modules were loaded, the correct fix is:

- fix the module configuration
- re-run detection

It is not correct to patch over that with a policy override.

### 3. The wrong binary is first in `PATH`

If detection found the wrong tool because the execution environment is contaminated, the correct fix is:

- clean or correct the environment
- re-run bootstrap

It is not a policy issue.

### 4. The user is unsure what the right value is

If you are not sure whether a value should differ from detection, do not override it yet.

A good override should feel intentional, not speculative.

---

## Decision rule

Ask this question:

> Should the final generated site intentionally differ from the real detected host?

If the answer is yes, an override may be appropriate.

If the answer is no, fix detection, configuration or environment instead.

---

## Platform overrides

### Use when

- the final site must intentionally target a different architecture
- the final site must intentionally normalize or pin a different operating system policy value

### Avoid when

- detection itself is wrong because the host environment was not prepared correctly
- you have not yet validated the detected facts

Example:

```yaml
site:
  policy_overrides:
    platform:
      operating_system: rhel8
      target: core2
```

---

## Runtime overrides

### Use when

- runtime locations must comply with institutional storage rules
- build/test/cache paths must be redirected to approved areas
- site-level build parallelism must be constrained or expanded intentionally

### Avoid when

- the detected runtime values are simply surprising but still valid
- the real issue is that the run was executed with the wrong user environment

---

## Provider overrides

### Use when

- the site has a formal provider choice for MPI
- the generated site must not follow detection preference order in a particular environment

### Avoid when

- the wrong provider was selected because package detection itself was wrong
- the environment was ambiguous and still not diagnosed

---

## External promotion mode is not the same thing as an override

This is important.

The choice between:

- `external_promotion_mode: all`
- `external_promotion_mode: providers-only`

is not a corrective override.
It is a normal policy choice.

Use it to choose how aggressive the site `packages.yaml` should be.

- use `all` when you want the site file to mirror the validated host stack more fully
- use `providers-only` when you want a more conservative site file for `spack-stack` usage

---

## Recommended workflow before writing an override

1. run bootstrap with `--debug`
2. read `detection-report.txt`
3. inspect detected facts
4. inspect derived policy
5. inspect authority and trace
6. decide whether the issue is:
   - a detection problem
   - an environment problem
   - a configuration problem
   - a legitimate institutional policy difference
7. only then write the override

This sequence avoids using overrides as a substitute for diagnosis.

---

## Good override mindset

A good override should satisfy all of these:

- it is intentional
- it is explainable
- it corresponds to institutional policy
- it would still make sense if another maintainer reads it later
- it is visible in the report authority and trace sections

If the override cannot be explained that way, it is probably the wrong fix.

---

## Practical examples

### Correct use

- detected host is `zen2`
- site must target `core2`
- override `platform.target`

### Incorrect use

- detected compiler is wrong because wrong module was loaded
- override compiler-related behavior instead of fixing modules

### Correct use

- runtime paths must live in `/scratch/site/...`
- override runtime paths

### Incorrect use

- HDF5 was detected from an unexpected prefix because `PATH` is dirty
- override around the result instead of fixing the environment

---

## Summary

Overrides are a policy tool, not a bandage.

Use them when:

- the final site must intentionally differ from the host

Do not use them when:

- detection is wrong
- the environment is wrong
- the configuration is incomplete
- you have not yet read the detection report

That discipline is what keeps `bootstrap-spack` useful in real production-oriented workflows.
