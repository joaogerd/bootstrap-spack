from __future__ import annotations

from pathlib import Path

import yaml

from bootstrap.domain.models import (
    CompilerEntry,
    DetectedPackage,
    Hdf5ValidationDetails,
    MpiValidationDetails,
    PackageSpec,
    SiteRuntimeConfig,
    ToolchainCheckResult,
    ValidationResult,
)
from bootstrap.services.bootstrap_service import BootstrapService


def _write_config(tmp_path: Path, *, promotion_mode: str) -> Path:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
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
validation:
  strict: true
site:
  name: integration-site
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  external_promotion_mode: {promotion_mode}
  core_compilers:
    - gcc@9.4.0
template:
  name: mpas-bundle
  specs:
    - mpas-bundle
  compiler: gcc
output:
  directory: .
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return config_file


def _detected_packages() -> dict[str, DetectedPackage]:
    return {
        "openmpi": DetectedPackage(
            name="openmpi",
            found=True,
            prefix="/opt/mpi",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=MpiValidationDetails(
                    prefix="/opt/mpi",
                    family="openmpi",
                    version="4.1.1",
                    version_line="Open MPI 4.1.1",
                    mpi_wrapper="/opt/mpi/bin/mpicc",
                    wrapper_show="gcc ...",
                ),
            ),
        ),
        "hdf5": DetectedPackage(
            name="hdf5",
            found=True,
            prefix="/opt/hdf5",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=Hdf5ValidationDetails(
                    prefix="/opt/hdf5",
                    parallel=True,
                    show="gcc ...",
                    config_head="HDF5 Version: 1.12.2",
                    version="1.12.2",
                ),
            ),
        ),
    }


def _specs() -> dict[str, PackageSpec]:
    return {
        "openmpi": PackageSpec(
            package="openmpi",
            spec="openmpi@4.1.1",
            prefix="/opt/mpi",
        ),
        "hdf5": PackageSpec(
            package="hdf5",
            spec="hdf5@1.12.2 ^openmpi@4.1.1",
            prefix="/opt/hdf5",
        ),
    }


def _compiler() -> CompilerEntry:
    return CompilerEntry(
        spec="gcc@9.4.0",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        f77="/usr/bin/gfortran",
        fc="/usr/bin/gfortran",
        operating_system="rhel8.4",
        target="x86_64",
        modules=["gnu9/9.4.0", "openmpi4/4.1.1"],
    )


def _runtime() -> SiteRuntimeConfig:
    return SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/integration-site/opt/spack",
        build_stage=["/scratch/user/spack-stack/integration-site/stage"],
        test_stage="/scratch/user/spack-stack/integration-site/test",
        source_cache="/home/user/.spack-stack/integration-site/cache/source",
        misc_cache="/home/user/.spack-stack/integration-site/cache/misc",
    )


def _prepare_monkeypatch(monkeypatch) -> None:
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.load_base_modules",
        lambda modules: {"PATH": "/usr/bin", "HOME": "/home/user", "USER": "user"},
    )
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.detect_requested_packages",
        lambda **kwargs: _detected_packages(),
    )
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_linkage_inspection", lambda **kwargs: {})
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.run_toolchain_check",
        lambda **kwargs: ToolchainCheckResult(valid=True, reason="toolchain consistente"),
    )
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_build_specs", lambda **kwargs: _specs())
    monkeypatch.setattr("bootstrap.services.bootstrap_service.detect_compiler_entry", lambda *args, **kwargs: _compiler())
    monkeypatch.setattr("bootstrap.services.bootstrap_service.detect_site_runtime_config", lambda *args, **kwargs: _runtime())



def test_bootstrap_service_external_promotion_mode_all(tmp_path: Path, monkeypatch) -> None:
    config_file = _write_config(tmp_path, promotion_mode="all")
    _prepare_monkeypatch(monkeypatch)

    service = BootstrapService(str(config_file))
    out_dir = tmp_path / "out_all"
    out_dir.mkdir()
    service.run(
        output_report=str(out_dir / "detection-report.txt"),
        output_yaml=str(out_dir / "packages.yaml"),
        dry_run=False,
        debug=False,
    )

    site_packages = yaml.safe_load(
        (out_dir / "configs" / "sites" / "integration-site" / "packages.yaml").read_text(encoding="utf-8")
    )
    packages = site_packages["packages"]

    assert packages["openmpi"]["buildable"] is False
    assert packages["openmpi"]["externals"][0]["prefix"] == "/opt/mpi"
    assert packages["hdf5"]["buildable"] is False
    assert packages["hdf5"]["externals"][0]["prefix"] == "/opt/hdf5"



def test_bootstrap_service_external_promotion_mode_providers_only(tmp_path: Path, monkeypatch) -> None:
    config_file = _write_config(tmp_path, promotion_mode="providers-only")
    _prepare_monkeypatch(monkeypatch)

    service = BootstrapService(str(config_file))
    out_dir = tmp_path / "out_providers_only"
    out_dir.mkdir()
    service.run(
        output_report=str(out_dir / "detection-report.txt"),
        output_yaml=str(out_dir / "packages.yaml"),
        dry_run=False,
        debug=False,
    )

    site_packages = yaml.safe_load(
        (out_dir / "configs" / "sites" / "integration-site" / "packages.yaml").read_text(encoding="utf-8")
    )
    packages = site_packages["packages"]

    assert packages["openmpi"]["buildable"] is False
    assert packages["openmpi"]["externals"][0]["prefix"] == "/opt/mpi"
    assert packages["hdf5"] == {"buildable": True}
