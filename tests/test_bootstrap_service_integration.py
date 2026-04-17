from pathlib import Path

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


def test_bootstrap_service_run_generates_layered_layout(tmp_path: Path, monkeypatch) -> None:
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
  name: linux-example
  layout: spack-stack
  module_system: lmod
  build_jobs: 8
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
        operating_system="linux",
        target="x86_64",
        modules=[],
    )
    runtime = SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/linux-example/opt/spack",
        build_stage=["/scratch/user/spack-stack/linux-example/stage"],
        test_stage="/scratch/user/spack-stack/linux-example/test",
        source_cache="/home/user/.spack-stack/linux-example/cache/source",
        misc_cache="/home/user/.spack-stack/linux-example/cache/misc",
    )

    monkeypatch.setattr("bootstrap.services.bootstrap_service.load_base_modules", lambda modules: {"PATH": "/usr/bin", "HOME": "/home/user", "USER": "user"})
    monkeypatch.setattr("bootstrap.services.bootstrap_service.detect_requested_packages", lambda **kwargs: detected)
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_linkage_inspection", lambda **kwargs: {})
    monkeypatch.setattr(
        "bootstrap.services.bootstrap_service.run_toolchain_check",
        lambda **kwargs: ToolchainCheckResult(valid=True, reason="toolchain consistente"),
    )
    monkeypatch.setattr("bootstrap.services.bootstrap_service.run_build_specs", lambda **kwargs: specs)
    monkeypatch.setattr("bootstrap.services.bootstrap_service.detect_compiler_entry", lambda *args, **kwargs: compiler)
    monkeypatch.setattr("bootstrap.services.bootstrap_service.detect_site_runtime_config", lambda *args, **kwargs: runtime)

    service = BootstrapService(str(config_file))
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    result = service.run(
        output_report=str(out_dir / "detection-report.txt"),
        output_yaml=str(out_dir / "packages.yaml"),
        dry_run=False,
        debug=False,
    )

    assert result.output_yaml == str(out_dir / "packages.yaml")
    assert (out_dir / "packages.yaml").exists()
    assert (out_dir / "detection-report.txt").exists()
    assert (out_dir / "configs" / "common" / "packages.yaml").exists()
    assert (out_dir / "configs" / "common" / "modules.yaml").exists()
    assert (out_dir / "configs" / "sites" / "linux-example" / "compilers.yaml").exists()
    assert (out_dir / "configs" / "sites" / "linux-example" / "config.yaml").exists()
    assert (out_dir / "configs" / "templates" / "mpas-bundle" / "spack.yaml").exists()

    config_text = (out_dir / "configs" / "sites" / "linux-example" / "config.yaml").read_text(encoding="utf-8")
    assert "install_tree" in config_text
    assert "/home/user/.spack-stack/linux-example/opt/spack" in config_text
