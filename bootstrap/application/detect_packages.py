from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from bootstrap.core.package_registry import build_package_registry_index, normalize_package_name
from bootstrap.domain.models import DetectedPackage, ExecutionContext, PackageDefinition, ValidationResult
from bootstrap.infrastructure.detection.package_detector import detect_package


def _unknown_detected(name: str, normalized: str, reason: str) -> DetectedPackage:
    return DetectedPackage(
        name=normalized,
        found=False,
        validation=ValidationResult(
            valid=False,
            reason=reason,
        ),
        metadata={
            # Kept as optional diagnostics; ignored by current renderers.
            "requested": name,
        },
    )


def _with_requested_as(pkg: DetectedPackage, requested_as: List[str]) -> DetectedPackage:
    if not requested_as:
        return pkg

    canonical = normalize_package_name(pkg.name)

    # Only annotate when the user did not request strictly the canonical name.
    if len(requested_as) == 1 and normalize_package_name(requested_as[0]) == canonical:
        return pkg

    meta = dict(pkg.metadata)
    meta["requested_as"] = list(requested_as)

    return DetectedPackage(
        name=pkg.name,
        found=pkg.found,
        prefix=pkg.prefix,
        method=pkg.method,
        tool_paths=dict(pkg.tool_paths),
        validation=pkg.validation,
        metadata=meta,
    )


def _detect_one(
    canonical_name: str,
    registry: Dict[str, PackageDefinition],
    context: ExecutionContext,
) -> tuple[str, DetectedPackage]:
    canonical = normalize_package_name(canonical_name)

    definition = registry.get(canonical)
    if definition is None:
        return (
            canonical,
            _unknown_detected(
                name=canonical_name,
                normalized=canonical,
                reason=f"unknown package: {canonical_name}",
            ),
        )

    return canonical, detect_package(definition, context)


def detect_requested_packages(
    requested: List[str],
    registry: Dict[str, PackageDefinition],
    context: ExecutionContext,
) -> Dict[str, DetectedPackage]:
    if not requested:
        return {}

    index = build_package_registry_index(registry)

    # Final output map. Keys are always normalized.
    detected: Dict[str, DetectedPackage] = {}

    # Canonical names to detect (deduplicated), with trace of what the user requested.
    to_detect: Dict[str, List[str]] = {}

    for raw in requested:
        resolution = index.resolve(raw)

        if resolution.resolved and resolution.canonical:
            canonical = resolution.canonical
            bucket = to_detect.setdefault(canonical, [])
            if raw not in bucket:
                bucket.append(raw)
            continue

        if resolution.status == "ambiguous":
            candidates = ", ".join(resolution.candidates) if resolution.candidates else ""
            reason = f"ambiguous package name: {raw}"
            if candidates:
                reason += f" (matches: {candidates})"

            detected[resolution.normalized] = _unknown_detected(
                name=raw,
                normalized=resolution.normalized,
                reason=reason,
            )
            continue

        # Unknown package: preserve current behavior (keep it in the output as buildable=True).
        detected[resolution.normalized] = _unknown_detected(
            name=raw,
            normalized=resolution.normalized,
            reason=f"unknown package: {raw}",
        )

    # Nothing resolvable: return only unknown/ambiguous entries.
    if not to_detect:
        return detected

    max_workers = max(1, min(4, len(to_detect)))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_detect_one, canonical, registry, context)
            for canonical in to_detect.keys()
        ]

        for future in as_completed(futures):
            canonical, result = future.result()
            detected[canonical] = _with_requested_as(result, to_detect.get(canonical, []))

    return detected

