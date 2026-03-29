from __future__ import annotations

from bootstrap.domain.models import ExecutionContext, PackageDefinition
from bootstrap.infrastructure.detection.package_detector import detect_package


def test_detect_unknown_package_tools_missing():
    context = ExecutionContext(
        base_env={},
        loaded_modules=[],
        strict_validation=False,
        platform=None,
    )

    definition = PackageDefinition(
        name="fakepkg",
        aliases=[],
        tools=["nonexistent-tool-xyz"],
        validation_type="mpi",
        family="test",
    )

    result = detect_package(definition, context)

    assert result.found is False
    assert result.validation is not None
    assert result.validation.valid is False
