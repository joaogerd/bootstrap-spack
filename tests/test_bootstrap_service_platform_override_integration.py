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


def test_bootstrap_service_platform_target_override_affects_rendered_compilers_yaml(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: cluster
modules:
  load:
    - gnu9/9.4.0
    - openmpi4/4.1.1
  optional: []
packages:
  external:
    - openmpi
validation:
  strict: true
site:
  name: override-site
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
  core_compilers:
    - gcc@9.4.0
  policy_overrides:
    platform:
      target: core2
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
        spec="gcc@9.4.0",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        f77="/usr/bin/gfortran",
        fc="/usr/bin/gfortran",
        operating_system="rhel8.4",
        target="x86_64",
        modules=["gnu9/9.4.0", "openmpi4/4.1.1"],
    )
    runtime = SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/override-site/opt/spack",
        build_stage=["/scratch/user/spack-stack/override-site/stage"],
        test_stage="/scratch/user/spack-stack/override-site/test",
        source_cache="/home/user/.spack-stack/override-site/cache/source",
        misc_cache="/home/user/.spack-stack/override-site/cache/misc",
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

    compilers_data = yaml.safe_load(
        (out_dir / "configs" / "sites" / "override-site" / "compilers.yaml").read_text(encoding="utf-8")
    )
    compiler_yaml = compilers_data["compilers"][0]["compiler"]

    assert compiler_yaml["operating_system"] == "rhel8"
    assert compiler_yaml["target"] == "core2"

    report_text = (out_dir / "detection-report.txt").read_text(encoding="utf-8")
    assert "platform.target" in report_text
    assert "source=override" in report_text
