# Changelog

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

