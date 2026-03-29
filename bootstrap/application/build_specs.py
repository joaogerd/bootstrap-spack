from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import DetectedPackage, PackageLinkage, PackageSpec
from bootstrap.infrastructure.spec.spec_builder import build_specs


def run_build_specs(
    detected: Dict[str, DetectedPackage],
    linkage: Dict[str, PackageLinkage],
) -> Dict[str, PackageSpec]:
    return build_specs(detected, linkage)
