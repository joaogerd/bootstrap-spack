from bootstrap.application.detect_packages import detect_requested_packages
from bootstrap.domain.models import DetectedPackage, ExecutionContext, ValidationResult


def test_detect_requested_packages_preserves_unknown_and_ambiguous_entries() -> None:
    registry = {}
    context = ExecutionContext(base_env={}, loaded_modules=[], strict_validation=False)

    detected = detect_requested_packages(
        requested=["mpi", "mystery"],
        registry=registry,
        context=context,
    )

    assert detected["mpi"].found is False
    assert detected["mpi"].validation.reason == "unknown package: mpi"
    assert detected["mystery"].found is False
    assert detected["mystery"].validation.reason == "unknown package: mystery"


def test_detect_requested_packages_annotates_requested_aliases(monkeypatch) -> None:
    from bootstrap.application import detect_packages as module
    from bootstrap.core.package_registry import PACKAGES

    def fake_detect_package(definition, context):
        return DetectedPackage(
            name=definition.name,
            found=True,
            prefix=f"/opt/{definition.name}",
            method="fake",
            validation=ValidationResult(valid=True, reason="ok"),
        )

    monkeypatch.setattr(module, "detect_package", fake_detect_package)

    context = ExecutionContext(base_env={}, loaded_modules=[], strict_validation=False)
    detected = detect_requested_packages(
        requested=["openmpi", "mpi"],
        registry=PACKAGES,
        context=context,
    )

    assert "openmpi" in detected
    assert detected["openmpi"].found is True
    assert detected["openmpi"].metadata["requested_as"] == ["openmpi", "mpi"]
