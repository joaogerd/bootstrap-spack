from pathlib import Path

import yaml

from bootstrap.domain.models import (
    CompilerEntry,
    DetectedPackage,
    MpiValidationDetails,
    PackageSpec,
    SiteConfig,
    SiteRuntimeConfig,
    TemplateConfig,
    ValidationResult,
)
from bootstrap.infrastructure.rendering.site_tree import write_site_tree


def test_write_site_tree_creates_layered_spack_stack_layout(tmp_path: Path) -> None:
    compiler = CompilerEntry(
        spec="gcc@9.4.0",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        f77="/usr/bin/gfortran",
        fc="/usr/bin/gfortran",
        operating_system="rhel8",
        target="x86_64",
        modules=["gnu9/9.4.0"],
    )
    runtime = SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/linux-example/opt/spack",
        build_stage=["/scratch/user/spack-stack/linux-example/stage"],
        test_stage="/scratch/user/spack-stack/linux-example/test",
        source_cache="/home/user/.spack-stack/linux-example/cache/source",
        misc_cache="/home/user/.spack-stack/linux-example/cache/misc",
    )
    site = SiteConfig(
        name="linux-example",
        layout="spack-stack",
        module_system="lmod",
        build_jobs=8,
        core_compilers=["gcc@9.4.0"],
    )
    template = TemplateConfig(
        name="mpas-bundle",
        specs=["mpas-bundle"],
        compiler="gcc",
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

    site_dir = write_site_tree(
        str(tmp_path),
        site=site,
        template=template,
        compiler=compiler,
        runtime_config=runtime,
        detected=detected,
        specs=specs,
    )

    assert site_dir is not None
    common_root = tmp_path / "configs" / "common"
    site_root = tmp_path / "configs" / "sites" / "linux-example"
    template_root = tmp_path / "configs" / "templates" / "mpas-bundle"

    assert Path(site_dir) == site_root
    assert (common_root / "packages.yaml").exists()
    assert (common_root / "modules.yaml").exists()
    assert (site_root / "packages.yaml").exists()
    assert (site_root / "compilers.yaml").exists()
    assert (site_root / "modules.yaml").exists()
    assert (site_root / "config.yaml").exists()
    assert (template_root / "spack.yaml").exists()

    common_packages = yaml.safe_load((common_root / "packages.yaml").read_text(encoding="utf-8"))
    assert common_packages["packages"]["all"]["providers"]["mpi"] == ["openmpi"]

    site_packages = yaml.safe_load((site_root / "packages.yaml").read_text(encoding="utf-8"))
    assert site_packages["packages"]["openmpi"]["externals"][0]["spec"] == "openmpi@4.1.1"

    compilers_data = yaml.safe_load((site_root / "compilers.yaml").read_text(encoding="utf-8"))
    assert compilers_data["compilers"][0]["compiler"]["spec"] == "gcc@9.4.0"

    site_modules = yaml.safe_load((site_root / "modules.yaml").read_text(encoding="utf-8"))
    assert site_modules["modules"]["default"]["lmod"]["core_compilers"] == ["gcc@9.4.0"]

    config_data = yaml.safe_load((site_root / "config.yaml").read_text(encoding="utf-8"))
    assert config_data["config"]["build_jobs"] == 8
    assert config_data["config"]["install_tree"]["root"] == "/home/user/.spack-stack/linux-example/opt/spack"
    assert config_data["config"]["build_stage"] == ["/scratch/user/spack-stack/linux-example/stage"]
    assert config_data["config"]["test_stage"] == "/scratch/user/spack-stack/linux-example/test"

    template_data = yaml.safe_load((template_root / "spack.yaml").read_text(encoding="utf-8"))
    assert template_data["spack"]["specs"] == ["mpas-bundle %gcc"]
