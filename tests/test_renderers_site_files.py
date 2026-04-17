import yaml

from bootstrap.domain.models import CompilerEntry
from bootstrap.infrastructure.rendering.compilers_yaml import generate_compilers_yaml
from bootstrap.infrastructure.rendering.config_yaml import generate_config_yaml
from bootstrap.infrastructure.rendering.modules_yaml import generate_modules_yaml


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


def test_generate_modules_yaml_for_lmod_includes_core_compilers() -> None:
    data = yaml.safe_load(generate_modules_yaml("lmod", ["gcc@9.4.0"]))

    assert data["modules"]["default"]["enable"] == ["lmod"]
    assert data["modules"]["default"]["lmod"]["core_compilers"] == ["gcc@9.4.0"]


def test_generate_config_yaml_contains_build_jobs() -> None:
    data = yaml.safe_load(generate_config_yaml(16))

    assert data == {"config": {"build_jobs": 16}}
