from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import DetectedPackage, PackageLinkage, ToolchainCheckResult
from bootstrap.domain.toolchain_policy import check_toolchain


def run_toolchain_check(
    detected: Dict[str, DetectedPackage],
    linkage: Dict[str, PackageLinkage],
) -> ToolchainCheckResult:
    return check_toolchain(list(detected.values()), linkage)
