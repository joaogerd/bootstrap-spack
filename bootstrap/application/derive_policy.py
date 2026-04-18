from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import (
    DerivedSitePolicy,
    DetectedHostFacts,
    DetectedPackage,
    ExecutionContext,
    PackageSpec,
    PolicyDecisionTrace,
)


def derive_policy_providers(detected: Dict[str, DetectedPackage]) -> Dict[str, list[str]]:
    providers: Dict[str, list[str]] = {}

    for preferred in ("openmpi", "mpich"):
        pkg = detected.get(preferred)
        if pkg and pkg.found:
            providers["mpi"] = [preferred]
            break

    return providers


def build_detected_host_facts(
    *,
    config,
    context: ExecutionContext,
    compiler,
    runtime_config,
    detected,
    linkage,
) -> DetectedHostFacts:
    return DetectedHostFacts(
        platform_family=config.platform,
        module_system=config.site.module_system if config.site.enabled else None,
        loaded_modules=list(context.loaded_modules),
        optional_modules=list(context.optional_modules),
        compiler=compiler,
        packages=dict(detected),
        linkage=dict(linkage),
        runtime=runtime_config,
    )


def derive_site_policy(*, config, facts: DetectedHostFacts, specs: Dict[str, PackageSpec]) -> DerivedSitePolicy:
    common_modules_enabled = [config.site.module_system] if config.site.enabled else []
    return DerivedSitePolicy(
        site=config.site,
        template=config.template,
        runtime=facts.runtime,
        compiler=facts.compiler,
        requested_packages=list(config.external_packages),
        packages=dict(specs),
        providers=derive_policy_providers(facts.packages),
        common_modules_enabled=common_modules_enabled,
    )


def build_policy_trace(*, config, facts: DetectedHostFacts, policy: DerivedSitePolicy, strict: bool) -> PolicyDecisionTrace:
    decisions = [
        f"platform_family set to {facts.platform_family or 'unknown'}",
        f"strict validation {'enabled' if strict else 'disabled'}",
    ]

    if facts.module_system:
        decisions.append(f"module system set to {facts.module_system}")
    if facts.compiler is not None:
        decisions.append(f"compiler entry derived as {facts.compiler.spec}")
    if facts.runtime is not None:
        decisions.append(f"runtime config derived for site {config.site.name or 'unspecified'}")
        decisions.append(f"build_jobs resolved to {facts.runtime.build_jobs}")
        decisions.append(f"install_tree_root resolved to {facts.runtime.install_tree_root}")
    if policy.providers:
        for virtual, provider_list in policy.providers.items():
            decisions.append(f"provider policy for {virtual} set to {provider_list}")
    if config.template.enabled:
        decisions.append(f"template policy enabled for {config.template.name or 'unnamed-template'}")

    assumptions = []
    for spec in policy.packages.values():
        assumptions.extend(spec.assumptions)

    warnings = []
    if not config.site.enabled:
        warnings.append("site generation disabled; policy is partial")
    if facts.module_system is None:
        warnings.append("module system not explicitly modeled for this host")
    if facts.runtime is None and config.site.enabled:
        warnings.append("runtime config unavailable; site policy is incomplete")

    return PolicyDecisionTrace(
        decisions=decisions,
        warnings=warnings,
        assumptions=sorted(set(assumptions)),
    )
