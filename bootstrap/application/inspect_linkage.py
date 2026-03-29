from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import DetectedPackage, ExecutionContext, PackageLinkage
from bootstrap.infrastructure.linkage.linkage_inspector import inspect_linkage


def run_linkage_inspection(
    detected: Dict[str, DetectedPackage],
    context: ExecutionContext,
) -> Dict[str, PackageLinkage]:
    linkage: Dict[str, PackageLinkage] = {}

    for name, pkg in detected.items():
        if not pkg.found:
            continue
        if not pkg.validation or not pkg.validation.valid:
            continue

        linkage[name] = inspect_linkage(pkg, context.base_env)

    return linkage
