from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from bootstrap.domain.models import DetectedPackage, ExecutionContext, PackageDefinition, ValidationResult
from bootstrap.infrastructure.detection.package_detector import detect_package


def _detect_one(
    name: str,
    registry: Dict[str, PackageDefinition],
    context: ExecutionContext,
) -> tuple[str, DetectedPackage]:
    normalized = name.lower()

    if normalized not in registry:
        return (
            normalized,
            DetectedPackage(
                name=normalized,
                found=False,
                validation=ValidationResult(
                    valid=False,
                    reason=f"unknown package: {name}",
                ),
            ),
        )

    definition = registry[normalized]
    return normalized, detect_package(definition, context)


def detect_requested_packages(
    requested: List[str],
    registry: Dict[str, PackageDefinition],
    context: ExecutionContext,
) -> Dict[str, DetectedPackage]:
    if not requested:
        return {}

    detected: Dict[str, DetectedPackage] = {}
    max_workers = max(1, min(4, len(requested)))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_detect_one, name, registry, context)
            for name in requested
        ]

        for future in as_completed(futures):
            name, result = future.result()
            detected[name] = result

    return detected
