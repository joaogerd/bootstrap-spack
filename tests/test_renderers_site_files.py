import yaml

from bootstrap.domain.models import (
    CompilerEntry,
    DerivedSitePolicy,
    DetectedPackage,
    MpiValidationDetails,
    PackageSpec,
    SiteConfig,
    SiteRuntimeConfig,
    TemplateConfig,
    ValidationResult,
)
from bootstrap.infrastructure.rendering.compilers_yaml import (
    generate_compilers_yaml,
    generate_compilers_yaml_from_policy,
)
from bootstrap.infrastructure.rendering.config_yaml import (
    generate_config_yaml,
    generate_config_yaml_from_policy,
)
from bootstrap.infrastructure.rendering.modules_yaml import (
    generate_common_modules_yaml,
    generate_modules_yaml,
    generate_site_modules_yaml,
)
from bootstrap.infrastructure.rendering.packages_yaml import (
    generate_common_packages_yaml,
    generate_site_packages_yaml,
)
from bootstrap.infrastructure.rendering.template_spack_yaml import generate_template_spack_yaml


def test_generate_compilers_yaml_renders_expected_structure() -> None:
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

    data = yaml.safe_load(generate_compilers_yaml([compiler]))

    assert "compilers" in data
    entry = data["compilers"][0]["compiler"]
    assert entry["spec"] == "gcc@9.4.0"
    assert entry["paths"]["cc"] == "/usr/bin/gcc"
    assert entry["modules"] == ["gnu9/9.4.0"]
    assert entry["operating_system"] == "rhel8"
    assert entry["target"] == "x86_64"


def test_generate_compilers_yaml_from_policy_uses_policy_compiler() -> None:
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
    policy = DerivedSitePolicy(
        site=SiteConfig(name="linux-example"),
        template=TemplateConfig(name="mpas-bundle", specs=["mpas-bundle"], compiler="gcc"),
        runtime=None,
        compiler=compiler,
        requested_packages=[],
        packages={},
        providers={},
        common_modules_enabled=["lmod"],
    )

    data = yaml.safe_load(generate_compilers_yaml_from_policy(policy))
    assert data["compilers"][0]["compiler"]["spec"] == "gcc@9.4.0"


def test_generate_common_and_site_modules_yaml_split_policy_and_site_facts() -> None:
    common = yaml.safe_load(generate_common_modules_yaml("lmod"))
    site = yaml.safe_load(generate_site_modules_yaml("lmod", ["gcc@9.4.0"]))
    merged = yaml.safe_load(generate_modules_yaml("lmod", ["gcc@9.4.0"]))

    assert common["modules"]["default"]["enable"] == ["lmod"]
    assert site["modules"]["default"]["lmod"]["core_compilers"] == ["gcc@9.4.0"]
    assert merged["modules"]["default"]["enable"] == ["lmod"]
    assert merged["modules"]["default"]["lmod"]["core_compilers"] == ["gcc@9.4.0"]


def test_generate_common_and_site_packages_yaml_split_policy_and_externals() -> None:
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

    common = yaml.safe_load(generate_common_packages_yaml(detected))
    site = yaml.safe_load(generate_site_packages_yaml(detected, specs))

    assert common["packages"]["all"]["providers"]["mpi"] == ["openmpi"]
    assert site["packages"]["openmpi"]["externals"][0]["spec"] == "openmpi@4.1.1"
    assert site["packages"]["openmpi"]["buildable"] is False


def test_generate_template_spack_yaml_renders_specs_with_compiler() -> None:
    data = yaml.safe_load(generate_template_spack_yaml(["mpas-bundle"], compiler="gcc"))
    assert data["spack"]["specs"] == ["mpas-bundle %gcc"]
    assert data["spack"]["view"] is False


def test_generate_config_yaml_contains_detected_runtime_policy() -> None:
    runtime = SiteRuntimeConfig(
        build_jobs=8,
        install_tree_root="/home/user/.spack-stack/egeon/opt/spack",
        build_stage=["/scratch/user/spack-stack/egeon/stage"],
        test_stage="/scratch/user/spack-stack/egeon/test",
        source_cache="/home/user/.spack-stack/egeon/cache/source",
        misc_cache="/home/user/.spack-stack/egeon/cache/misc",
    )
    data = yaml.safe_load(generate_config_yaml(runtime))

    assert data["config"]["build_jobs"] == 8
    assert data["config"]["install_tree"]["root"] == "/home/user/.spack-stack/egeon/opt/spack"
    assert data["config"]["build_stage"] == ["/scratch/user/spack-stack/egeon/stage"]
    assert data["config"]["test_stage"] == "/scratch/user/spack-stack/egeon/test"
    assert data["config"]["source_cache"] == "/home/user/.spack-stack/egeon/cache/source"
    assert data["config"]["misc_cache"] == "/home/user/.spack-stack/egeon/cache/misc"


def test_generate_config_yaml_from_policy_falls_back_to_site_build_jobs_only() -> None:
    policy = DerivedSitePolicy(
        site=SiteConfig(name="linux-example", build_jobs=12),
        template=TemplateConfig(name="mpas-bundle", specs=["mpas-bundle"], compiler="gcc"),
        runtime=None,
        compiler=None,
        requested_packages=[],
        packages={},
        providers={},
        common_modules_enabled=["lmod"],
    )

    data = yaml.safe_load(generate_config_yaml_from_policy(policy))
    assert data["config"]["build_jobs"] == 12
    assert "install_tree" not in data["config"]
