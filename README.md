# bootstrap-spack

Detect external HPC libraries (MPI, HDF5, NetCDF, etc.) and generate:

- `packages.yaml` for Spack
- detailed detection report

## 🚀 Features

- Module-aware detection (Lmod / Environment Modules)
- Validation via:
  - wrapper inspection
  - optional compile tests (strict mode)
- Linkage inspection via `ldd`
- Automatic spec generation
- Toolchain consistency checks
- Parallel detection
- Timeout + retry for shell commands

---

## 📦 Installation

```bash
pip install -e .
````

---

## ⚙️ Usage

```bash
bootstrap --config env/egeon.yaml
```

### Options

```bash
--config <file>                YAML config (required)
--output-dir <dir>             Output directory (default: .)
--report-name <file>           Report filename
--packages-yaml-name <file>    packages.yaml filename
--strict true|false            Override strict validation
--dry-run                      Do not write files
--debug                        Verbose logging
```

---

## 📄 Example config

```yaml
platform: cray

modules:
  load:
    - cray-mpich
    - cray-hdf5-parallel

packages:
  external:
    - openmpi
    - hdf5
    - netcdf-c
    - netcdf-fortran

validation:
  strict: true
```

---

## 📤 Outputs

### packages.yaml

Used directly by Spack:

```yaml
packages:
  hdf5:
    externals:
      - spec: hdf5@1.12.2+mpi
        prefix: /opt/cray/hdf5
    buildable: false
```

---

### detection-report.txt

Human-readable diagnostics:

```
PACKAGE=hdf5
  found=True
  prefix=/opt/cray/hdf5
  parallel=True
```

---

## 🧠 Design

Layered architecture:

* `domain` → core models
* `application` → use cases
* `infrastructure` → shell / modules / validation
* `services` → orchestration
* `interfaces` → CLI

---

## ⚠️ Limitations (0.1.0)

* Heuristic spec reconstruction
* Limited compiler modeling
* No persistent cache
* Partial MPI family inference

---

## 🗺️ Roadmap

* Plugin system for detectors
* Persistent cache
* Full compiler/toolchain modeling
* Spack integration
* CI with real HPC environments

---

## 📜 License

MIT


