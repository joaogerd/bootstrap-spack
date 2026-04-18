from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Dict, List, Optional

from bootstrap.domain.models import (
    DerivedSitePolicy,
    DetectedHostFacts,
    DetectedPackage,
    PackageLinkage,
    PackageSpec,
    PolicyDecisionTrace,
    ToolchainCheckResult,
)


def _write_header(fh, platform: str | None, modules: List[str]) -> None:
    fh.write("=== BOOTSTRAP DETECTION REPORT ===\n\n")
    fh.write(f"platform={platform or ''}\n")
    fh.write(f"modules={modules}\n\n")


def _write_details_block(fh, prefix: str, payload: object) -> None:
    if not is_dataclass(payload):
        return
    for key, value in asdict(payload).items():
        if value in (None, "", [], {}):
            continue
        fh.write(f"  {prefix}{key}={value}\n")


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

        if pkg.validation and pkg.validation.warnings:
            fh.write(f"  warnings={pkg.validation.warnings}\n")

        requested_as = pkg.metadata.get("requested_as")
        if requested_as:
            fh.write(f"  requested_as={requested_as}\n")

        if pkg.validation and pkg.validation.details is not None:
            _write_details_block(fh, "detail_", pkg.validation.details)
        else:
            for key, value in pkg.metadata.items():
                if key in {"requested_as", "compile"}:
                    continue
                if value in (None, "", [], {}):
                    continue
                fh.write(f"  {key}={value}\n")

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
            fh.write(f"  spec_confidence={spec.confidence}\n")
            if spec.assumptions:
                fh.write(f"  spec_assumptions={spec.assumptions}\n")

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


def _write_facts(fh, facts: Optional[DetectedHostFacts]) -> None:
    if facts is None:
        return

    fh.write("=== FACTS ===\n\n")
    fh.write(f"platform_family={facts.platform_family or ''}\n")
    fh.write(f"module_system={facts.module_system or ''}\n")
    fh.write(f"loaded_modules={facts.loaded_modules}\n")
    fh.write(f"optional_modules={facts.optional_modules}\n")

    if facts.compiler is not None:
        _write_details_block(fh, "compiler_", facts.compiler)
    if facts.runtime is not None:
        _write_details_block(fh, "runtime_", facts.runtime)

    fh.write("\n")


def _write_policy(fh, policy: Optional[DerivedSitePolicy]) -> None:
    if policy is None:
        return

    fh.write("=== POLICY ===\n\n")
    fh.write(f"site_name={policy.site.name or ''}\n")
    fh.write(f"site_layout={policy.site.layout}\n")
    fh.write(f"requested_packages={policy.requested_packages}\n")
    fh.write(f"providers={policy.providers}\n")
    fh.write(f"common_modules_enabled={policy.common_modules_enabled}\n")

    if policy.compiler is not None:
        fh.write(f"policy_compiler={policy.compiler.spec}\n")
    if policy.runtime is not None:
        fh.write(f"policy_build_jobs={policy.runtime.build_jobs}\n")
        fh.write(f"policy_install_tree_root={policy.runtime.install_tree_root}\n")
    if policy.template.enabled:
        fh.write(f"template_name={policy.template.name or ''}\n")
        fh.write(f"template_specs={policy.template.specs}\n")
        fh.write(f"template_compiler={policy.template.compiler or ''}\n")

    fh.write("\n")


def _write_trace(fh, trace: Optional[PolicyDecisionTrace]) -> None:
    if trace is None:
        return

    fh.write("=== POLICY TRACE ===\n\n")
    if trace.decisions:
        fh.write(f"decisions={trace.decisions}\n")
    if trace.warnings:
        fh.write(f"warnings={trace.warnings}\n")
    if trace.assumptions:
        fh.write(f"assumptions={trace.assumptions}\n")
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
    facts: Optional[DetectedHostFacts] = None,
    policy: Optional[DerivedSitePolicy] = None,
    trace: Optional[PolicyDecisionTrace] = None,
) -> None:
    with open(output_file, "w", encoding="utf-8") as fh:
        _write_header(fh, platform, modules)
        _write_packages(fh, detected, linkage, specs)
        _write_toolchain(fh, toolchain)
        _write_facts(fh, facts)
        _write_policy(fh, policy)
        _write_trace(fh, trace)
