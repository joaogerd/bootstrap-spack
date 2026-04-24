from __future__ import annotations

from pathlib import Path

import yaml

from bootstrap.domain.models import (
    CompilerEntry,
    DetectedPackage,
    MpiValidationDetails,
    PackageSpec,
    SiteRuntimeConfig,
    ToolchainCheckResult,
    ValidationResult,
)
from bootstrap.services.bootstrap_service import BootstrapService


def test_bootstrap_service_linux_fixture_outputs_expected_artifacts(tmp_path: Path, monkeypatch) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: linux
modules:
  load: []
  optional: []
packages:
  external:
    - openmpi
validation:
  strict: true
site:
  name: linux-fixture
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  external_promotion_mode: all
  core_compilers:
    - gcc@12.3.0
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

    detected = {
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
        )
    }
    specs = {
        "openmpi": PackageSpec(
            package="openmpi",
            spec="openmpi@4.1.1",
            prefix="/opt/mpi",
        )
    }
    compiler = CompilerEntry(
        spec="gcc@12.3.0",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        f77="/usr/bin/gfortran",
        fc="/usr/bin/gfortran",
        operating_system="ubuntu22.04",
        target="x86_64",
        modules=[],
    )
    runtime = SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/linux-fixture/opt/spack",
        build_stage=["/tmp/user/spack-stack/linux-fixture/stage"],
        test_stage="/tmp/user/spack-stack/linux-fixture/test",
        source_cache="/home/user/.spack-stack/linux-fixture/cache/source",
        misc_cache="/home/user/.spack-stack/linux-fixture/cache/misc",
    )

    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.load_base_modules",
        lambda modules: {"PATH": "/usr/bin", "HOME": "/home/user", "USER": "user"},
    )
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.detect_requested_packages",
        lambda **kwargs: detected,
    )
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_linkage_inspection", lambda **kwargs: {})
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.run_toolchain_check",
        lambda **kwargs: ToolchainCheckResult(valid=True, reason="toolchain consistente"),
    )
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_build_specs", lambda **kwargs: specs)
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.detect_compiler_entry",
        lambda *args, **kwargs: compiler,
    )
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.detect_site_runtime_config",
        lambda *args, **kwargs: runtime,
    )

    service = BootstrapService(str(config_file))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    service.run(
        output_report=str(out_dir / "detection-report.txt"),
        output_yaml=str(out_dir / "packages.yaml"),
        dry_run=False,
        debug=False,
    )

    root_packages = yaml.safe_load((out_dir / "packages.yaml").read_text(encoding="utf-8"))
    common_packages = yaml.safe_load((out_dir / "configs" / "common" / "packages.yaml").read_text(encoding="utf-8"))
    common_modules = yaml.safe_load((out_dir / "configs" / "common" / "modules.yaml").read_text(encoding="utf-8"))
    site_packages = yaml.safe_load((out_dir / "configs" / "sites" / "linux-fixture" / "packages.yaml").read_text(encoding="utf-8"))
    site_compilers = yaml.safe_load((out_dir / "configs" / "sites" / "linux-fixture" / "compilers.yaml").read_text(encoding="utf-8"))
    site_modules = yaml.safe_load((out_dir / "configs" / "sites" / "linux-fixture" / "modules.yaml").read_text(encoding="utf-8"))
    site_config = yaml.safe_load((out_dir / "configs" / "sites" / "linux-fixture" / "config.yaml").read_text(encoding="utf-8"))
    template_yaml = yaml.safe_load((out_dir / "configs" / "templates" / "mpas-bundle" / "spack.yaml").read_text(encoding="utf-8"))

    assert root_packages["packages"]["all"]["providers"]["mpi"] == ["openmpi"]
    assert root_packages["packages"]["openmpi"]["externals"][0]["prefix"] == "/opt/mpi"

    assert common_packages == {"packages": {"all": {"providers": {"mpi": ["openmpi"]}}}}
    assert common_modules == {"modules": {"default": {"enable": ["lmod"]}}}

    assert site_packages["packages"]["openmpi"]["buildable"] is False
    assert site_packages["packages"]["openmpi"]["externals"][0]["spec"] == "openmpi@4.1.1"

    compiler_yaml = site_compilers["compilers"][0]["compiler"]
    assert compiler_yaml["spec"] == "gcc@12.3.0"
    assert compiler_yaml["operating_system"] == "ubuntu22.04"
    assert compiler_yaml["target"] == "x86_64"
    assert compiler_yaml["modules"] == []

    assert site_modules["modules"]["default"]["enable"] == ["lmod"]
    assert site_modules["modules"]["default"]["lmod"]["core_compilers"] == ["gcc@12.3.0"]

    assert site_config["config"]["build_jobs"] == 8
    assert site_config["config"]["install_tree"]["root"] == "/home/user/.spack-stack/linux-fixture/opt/spack"
    assert site_config["config"]["build_stage"] == ["/tmp/user/spack-stack/linux-fixture/stage"]
    assert site_config["config"]["test_stage"] == "/tmp/user/spack-stack/linux-fixture/test"
    assert site_config["config"]["source_cache"] == "/home/user/.spack-stack/linux-fixture/cache/source"
    assert site_config["config"]["misc_cache"] == "/home/user/.spack-stack/linux-fixture/cache/misc"

    assert template_yaml == {"spack": {"specs": ["mpas-bundle %gcc"]}}

    report_text = (out_dir / "detection-report.txt").read_text(encoding="utf-8")
    assert "=== FACTS ===" in report_text
    assert "=== POLICY ===" in report_text
    assert "=== POLICY AUTHORITY ===" in report_text
    assert "=== POLICY TRACE ===" in report_text
