from __future__ import annotations

from typing import Dict, List

from bootstrap.domain.models import DetectedPackage, PackageLinkage, PackageSpec, ToolchainCheckResult


def _write_header(fh, platform: str | None, modules: List[str]) -> None:
    fh.write("=== BOOTSTRAP DETECTION REPORT ===\n\n")
    fh.write(f"platform={platform or ''}\n")
    fh.write(f"modules={modules}\n\n")


def _write_packages(
    fh,
    detected: Dict[str, DetectedPackage],
    linkage: Dict[str, PackageLinkage],
    specs: Dict[str, PackageSpec],
) -> None:
    fh.write("=== PACKAGES ===\n\n")

    for name, pkg in detected.items():
        validation_reason = pkg.validation.reason if pkg.validation else ""
        fh.write(f"PACKAGE={name}\n")
        fh.write(f"  found={pkg.found}\n")
        fh.write(f"  method={pkg.method or ''}\n")
        fh.write(f"  prefix={pkg.prefix or ''}\n")
        fh.write(f"  reason={validation_reason}\n")

        version = pkg.metadata.get("version")
        if version:
            fh.write(f"  version={version}\n")

        family = pkg.metadata.get("family")
        if family:
            fh.write(f"  family={family}\n")

        pkg_linkage = linkage.get(name)
        if pkg_linkage:
            if pkg_linkage.hdf5_prefix:
                fh.write(f"  linked_hdf5={pkg_linkage.hdf5_prefix}\n")
            if pkg_linkage.mpi_prefix:
                fh.write(f"  linked_mpi={pkg_linkage.mpi_prefix}\n")
            if pkg_linkage.netcdf_c_prefix:
                fh.write(f"  linked_netcdf_c={pkg_linkage.netcdf_c_prefix}\n")

        spec = specs.get(name)
        if spec:
            fh.write(f"  spec={spec.spec}\n")

        fh.write("\n")


def _write_toolchain(fh, toolchain: ToolchainCheckResult) -> None:
    fh.write("=== TOOLCHAIN ===\n\n")
    fh.write(f"valid={toolchain.valid}\n")
    fh.write(f"reason={toolchain.reason}\n")
    fh.write(f"tokens={toolchain.tokens}\n")

    if toolchain.warnings:
        fh.write(f"warnings={toolchain.warnings}\n")

    if toolchain.problems:
        fh.write(f"problems={toolchain.problems}\n")

    fh.write("\n")


def write_detection_report(
    output_file: str,
    *,
    platform: str | None,
    modules: List[str],
    detected: Dict[str, DetectedPackage],
    linkage: Dict[str, PackageLinkage],
    specs: Dict[str, PackageSpec],
    toolchain: ToolchainCheckResult,
) -> None:
    with open(output_file, "w", encoding="utf-8") as fh:
        _write_header(fh, platform, modules)
        _write_packages(fh, detected, linkage, specs)
        _write_toolchain(fh, toolchain)
