# Changelog

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
