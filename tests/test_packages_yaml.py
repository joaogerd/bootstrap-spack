import yaml

from bootstrap.domain.models import DetectedPackage, MpiValidationDetails, PackageSpec, ValidationResult
from bootstrap.infrastructure.rendering.packages_yaml import generate_packages_yaml


def test_generate_packages_yaml_renders_external_and_sets_mpi_provider_from_validated_family() -> None:
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
        ),
    }
    specs = {
        "openmpi": PackageSpec(
            package="openmpi",
            spec="openmpi@4.1.1",
            prefix="/opt/mpi",
        )
    }

    rendered = yaml.safe_load(generate_packages_yaml(detected, specs))

    assert rendered["packages"]["all"]["providers"]["mpi"] == ["openmpi"]
    assert rendered["packages"]["openmpi"] == {
        "externals": [{"spec": "openmpi@4.1.1", "prefix": "/opt/mpi"}],
        "buildable": False,
    }


def test_generate_packages_yaml_marks_unknown_or_invalid_entries_as_buildable() -> None:
    detected = {
        "mystery": DetectedPackage(
            name="mystery",
            found=False,
            validation=ValidationResult(valid=False, reason="unknown package"),
        )
    }

    rendered = yaml.safe_load(generate_packages_yaml(detected, specs={}))

    assert "all" not in rendered["packages"]
    assert rendered["packages"]["mystery"] == {"buildable": True}
