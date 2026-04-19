# Changelog

## [0.4.0] - 2026-04-18

### Added

- Explicit policy-engineering architecture centered on:
  - `DetectedHostFacts`
  - `DerivedSitePolicy`
  - `PolicyDecisionTrace`
  - `PolicyAuthority`
  - `PolicyDerivationBundle`
- Structured policy trace entries with:
  - `message`
  - `source`
  - `rationale`
  - `confidence`
  - `fallback_used`
- Explicit policy authority metadata for important derived fields, including:
  - source
  - rationale
  - confidence
  - precedence rank
  - fallback usage
  - override attribution
  - superseded source
  - legacy compatibility usage
- Controlled site policy overrides via YAML under:
  - `site.policy_overrides.providers`
  - `site.policy_overrides.runtime`
- Authority precedence model for policy reporting:
  - `legacy-compat`
  - `default`
  - `policy`
  - `detection`
  - `config`
  - `override`
- Authority consistency warnings in policy trace when:
  - an unexpected source resolves a field
  - override is used where not allowed
  - legacy compatibility affects a field
  - the preferred source is not the one that won
- Report sections for:
  - detected host facts
  - derived policy
  - policy authority
  - policy trace
  - structured trace entries

### Changed

- Evolved the project from “explicit architecture” into the first real **policy-engineering** release line
- Refactored policy derivation into a clearer application-layer workflow
- Moved core generation flow further toward **policy-driven rendering**
- Updated unified and layered output generation to rely more directly on derived policy objects
- Improved semantic distinction between:
  - detected host facts
  - derived site policy
  - rendered artifacts
- Improved release narrative and README to reflect the new 0.4.x direction
- Strengthened auditability of the bootstrap result by exposing:
  - facts
  - policy
  - authority
  - trace

### Fixed

- Reduced silent decision-making in policy derivation by making source and rationale explicit
- Reduced hidden override behavior by promoting override to a formal authority layer
- Improved traceability of runtime and MPI provider decisions
- Improved consistency between real project state, versioning, and public documentation

### Validation

- Verified in real environments including:
  - generic Linux
  - EGEON
  - JACI
- Automated test suite passing for:
  - bootstrap service integration
  - config loading
  - package detection
  - renderer flow
  - site tree generation
  - runtime config
  - policy/authority related behavior

### Current status

This release marks the first version where the project is not only operationally useful, but also **semantically explicit** in how it derives site policy.

The bootstrap now works around a clear internal flow:

- requested configuration
- detected host facts
- derived site policy
- policy authority
- policy trace
- rendered artifacts

It also supports controlled override handling for central runtime and provider policy decisions.

### Focus of the 0.4.x line

The 0.4.x line is focused on **policy engineering**, especially:

- making derivation rules more explicit
- improving authority semantics
- expanding controlled overrides
- reducing legacy compatibility residue
- improving explainability and auditability of site policy decisions


## [0.3.0] - 2026-04-18

### Added

- Explicit architecture models for:
  - `DetectedHostFacts`
  - `DerivedSitePolicy`
  - `PolicyDecisionTrace`
  - `PolicyDerivationBundle`
- Detection report sections for:
  - `FACTS`
  - `POLICY`
  - `POLICY TRACE`
- Explicit policy derivation layer separating:
  - observed host facts
  - derived site policy
  - rendered artifacts
- Policy-aware site generation using derived policy as the central input
- Structured runtime policy reporting, including:
  - build jobs
  - install tree root
  - build stage
  - test stage
  - source cache
  - misc cache
- Support for explicit reporting of:
  - loaded base modules
  - optional module candidates
  - detected compiler entry
  - selected provider policy
- Bootstrap result enrichment with:
  - detected facts
  - derived policy
  - policy decision trace
- Expanded release documentation describing:
  - internal architecture
  - validation scope
  - current support maturity

### Changed

- Evolved the project from an operational layered bootstrap into an explicitly modeled architecture with three core semantic stages:
  - detection
  - policy derivation
  - artifact rendering
- Refactored site-tree generation to consume derived policy instead of loosely passing compiler, runtime and package pieces independently
- Refactored `packages.yaml` generation to be driven by policy instead of ad hoc assembly
- Improved architectural clarity by making policy decisions inspectable instead of implicit in the bootstrap flow
- Improved the bootstrap service so that the internal execution order now reflects the real conceptual pipeline:
  - load configuration
  - detect environment and packages
  - detect compiler and runtime
  - build detected facts
  - derive policy
  - generate decision trace
  - render artifacts
- Improved release documentation to reflect the real state of the project as a multi-platform bootstrap tool for:
  - Linux
  - EGEON
  - JACI / Cray-like environments

### Fixed

- Fixed residual API mismatch in site-tree tests after migration to policy-driven artifact generation
- Fixed architectural leakage where rendering still depended too directly on low-level detection structures
- Improved consistency between bootstrap outputs and the internal semantic model
- Stabilized the policy-driven generation path with passing tests after refactor

### Validation

- Verified in real environments including:
  - generic Linux
  - EGEON
  - JACI
- Test suite passing after the policy-driven refactor
- Release version updated to `0.3.0` in `pyproject.toml`

### Current status

This release is the first one where the project becomes not only operationally mature, but also architecturally explicit.

The bootstrap now distinguishes clearly between:

- what was requested by configuration
- what was detected from the host
- what was derived as site policy
- what was rendered as final configuration artifacts

The project now provides:

- real multi-platform bootstrap behavior
- layered spack-stack-style output generation
- explicit detection/policy/render separation
- auditable decision reporting
- policy-driven artifact generation

### Next architectural step

The next development cycle can now focus on strengthening the policy layer instead of introducing basic structural concepts.

The most natural next steps are:

- enrich `DerivedSitePolicy` into a more semantic policy model
- make policy derivation rules more explicit and extensible
- reduce remaining dependence on compatibility-oriented metadata paths
- improve platform-profile documentation and support maturity classification

## [0.2.0] - 2026-04-17

### Added

- Layered spack-stack-style output generation with:
  - `configs/common/`
  - `configs/sites/<site>/`
  - `configs/templates/<template>/`
- `SiteConfig`, `TemplateConfig`, `SiteRuntimeConfig` and `LayeredSpackStackArtifacts` domain models
- Template-aware configuration with support for:
  - `template.name`
  - `template.specs`
  - `template.compiler`
- Site runtime detection for generated `config.yaml`, including:
  - build jobs
  - install tree root
  - build stage
  - test stage
  - source cache
  - misc cache
- Compiler detection paths adapted for generic Linux and Cray-like environments
- Site tree artifact builder separated from filesystem writing
- Professional project README aligned with the current architecture and outputs
- Expanded automated test coverage for:
  - package registry
  - package detection flow
  - packages YAML rendering
  - command runner behavior
  - site config loading
  - layered site/tree rendering

### Changed

- Evolved the project from a single-output bootstrap utility into a layered Spack and spack-stack-oriented bootstrap workflow
- Split `packages.yaml` generation into:
  - common policy generation
  - site-specific external package generation
  - unified compatibility output
- Split `modules.yaml` generation into:
  - common module policy
  - site-specific module policy
  - unified compatibility output
- Improved compiler family and version inference using wrapper and platform evidence
- Improved module handling by preserving the parent shell environment during module operations and sanitizing only after the loaded environment is captured
- Restricted supported site layout handling to the explicit `spack-stack` model

### Fixed

- Corrected typed prefix patching in validation results using safe dataclass replacement
- Corrected alias coverage in tests for ambiguous versus non-ambiguous registry entries
- Improved compatibility on real HPC systems where module operations depend on full parent shell environment
- Stabilized renderer and site-tree flows with layered output coverage in tests

### Validation

- Verified in real environments including:
  - generic Linux
  - EGEON
  - JACI
- Test suite expanded and passing for the current bootstrap core and layered renderer flow

### Current status

This release is considered the first mature operational version of the project.

The bootstrap now works in real environments and supports:

- external package detection
- validation and linkage inspection
- unified Spack `packages.yaml` generation
- layered spack-stack-style site generation

### Next architectural step

The next development cycle is focused on making the architecture more explicit by introducing central domain models for:

- `DetectedHostFacts`
- `DerivedSitePolicy`
- `PolicyDecisionTrace`

These changes will separate:

- observed host facts
- derived site policy
- rendered artifacts

while preserving compatibility with the current workflow.

## [0.1.0] - Initial stable release

### Added

- Modular architecture (domain / application / infrastructure)
- YAML-based environment configuration
- Module system integration (Lmod / modules)
- Package detection pipeline
- Validation system:
  - MPI
  - HDF5
  - NetCDF-C
  - NetCDF-Fortran
- Optional strict validation (compile tests)
- Linkage inspection via ldd
- Spec builder for Spack
- Toolchain consistency checks
- packages.yaml generator
- Human-readable detection report
- Parallel detection
- CommandRunner with timeout + retry
- CLI interface

### Fixed

- Inconsistent subprocess usage → centralized runner
- Thread-unsafe cache → removed
- CLI strict flag ambiguity
- Environment contamination issues
- Module loading isolation

### Known limitations

- Heuristic spec generation
- Limited ABI/compiler awareness
- No persistent caching
- Partial MPI detection heuristics
