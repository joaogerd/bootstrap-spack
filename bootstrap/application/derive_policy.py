from __future__ import annotations

from typing import Dict, List, Optional

from bootstrap.domain.models import (
    DerivedSitePolicy,
    DetectedHostFacts,
    DetectedPackage,
    ExecutionContext,
    PackageSpec,
    PolicyAuthority,
    PolicyDecisionTrace,
    PolicyDerivationBundle,
    PolicyTraceEntry,
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


def _build_policy_authority(*, config, facts: DetectedHostFacts, providers: Dict[str, list[str]]) -> Dict[str, PolicyAuthority]:
    authority: Dict[str, PolicyAuthority] = {}

    if facts.module_system:
        authority["module_system"] = PolicyAuthority(
            key="module_system",
            value=facts.module_system,
            source="config",
            rationale="module backend declared in site configuration",
            confidence="high",
        )

    if facts.compiler is not None:
        authority["compiler"] = PolicyAuthority(
            key="compiler",
            value=facts.compiler.spec,
            source="detection",
            rationale="compiler entry inferred from active host toolchain",
            confidence="medium" if facts.platform_family in {"cray", "cluster"} else "high",
        )

    if facts.runtime is not None:
        authority["runtime.build_jobs"] = PolicyAuthority(
            key="runtime.build_jobs",
            value=str(facts.runtime.build_jobs),
            source="policy",
            rationale="build jobs derived from detected host capacity and site limits",
            confidence="medium",
            fallback_used="site.build_jobs" if facts.runtime.build_jobs == config.site.build_jobs else None,
        )
        authority["runtime.install_tree_root"] = PolicyAuthority(
            key="runtime.install_tree_root",
            value=facts.runtime.install_tree_root,
            source="policy",
            rationale="install tree root derived from detected runtime policy",
            confidence="medium",
        )
        authority["runtime.build_stage"] = PolicyAuthority(
            key="runtime.build_stage",
            value=str(facts.runtime.build_stage),
            source="policy",
            rationale="build stage derived from detected scratch and temporary paths",
            confidence="medium",
        )
        authority["runtime.test_stage"] = PolicyAuthority(
            key="runtime.test_stage",
            value=facts.runtime.test_stage,
            source="policy",
            rationale="test stage derived from detected scratch and temporary paths",
            confidence="medium",
        )

    if "mpi" in providers:
        authority["providers.mpi"] = PolicyAuthority(
            key="providers.mpi",
            value=str(providers["mpi"]),
            source="policy",
            rationale="provider chosen from validated MPI implementations using current provider selection rule",
            confidence="medium",
            fallback_used="preference order: openmpi -> mpich",
        )

    common_modules_enabled = [config.site.module_system] if config.site.enabled else []
    if common_modules_enabled:
        authority["common_modules_enabled"] = PolicyAuthority(
            key="common_modules_enabled",
            value=str(common_modules_enabled),
            source="policy",
            rationale="common module policy derived from site module backend",
            confidence="high",
        )

    if config.template.enabled:
        authority["template.enabled"] = PolicyAuthority(
            key="template.enabled",
            value=config.template.name or "unnamed-template",
            source="config",
            rationale="template section is enabled in bootstrap configuration",
            confidence="high",
        )

    return authority


def derive_site_policy(*, config, facts: DetectedHostFacts, specs: Dict[str, PackageSpec]) -> DerivedSitePolicy:
    common_modules_enabled = [config.site.module_system] if config.site.enabled else []
    providers = derive_policy_providers(facts.packages)
    authority = _build_policy_authority(config=config, facts=facts, providers=providers)

    return DerivedSitePolicy(
        site=config.site,
        template=config.template,
        runtime=facts.runtime,
        compiler=facts.compiler,
        requested_packages=list(config.external_packages),
        packages=dict(specs),
        providers=providers,
        common_modules_enabled=common_modules_enabled,
        authority=authority,
    )


def _trace_entry(
    message: str,
    *,
    source: str,
    rationale: str,
    confidence: str = "high",
    fallback_used: Optional[str] = None,
) -> PolicyTraceEntry:
    return PolicyTraceEntry(
        message=message,
        source=source,
        rationale=rationale,
        confidence=confidence,
        fallback_used=fallback_used,
    )


def _build_trace_entries(*, config, facts: DetectedHostFacts, policy: DerivedSitePolicy, strict: bool) -> List[PolicyTraceEntry]:
    entries: List[PolicyTraceEntry] = [
        _trace_entry(
            f"platform_family set to {facts.platform_family or 'unknown'}",
            source="config",
            rationale="platform profile requested by bootstrap configuration",
            confidence="high" if facts.platform_family else "heuristic",
        ),
        _trace_entry(
            f"strict validation {'enabled' if strict else 'disabled'}",
            source="config",
            rationale="validation mode requested by bootstrap configuration",
        ),
        _trace_entry(
            f"requested packages count={len(policy.requested_packages)}",
            source="config",
            rationale="external package request list parsed from bootstrap configuration",
        ),
        _trace_entry(
            f"validated external packages count={len(policy.packages)}",
            source="detection",
            rationale="count derived from validated package specs",
            confidence="medium",
        ),
    ]

    if facts.loaded_modules:
        entries.append(
            _trace_entry(
                f"base modules loaded={facts.loaded_modules}",
                source="detection",
                rationale="base module environment captured before package validation",
            )
        )
    if facts.optional_modules:
        entries.append(
            _trace_entry(
                f"optional module candidates={facts.optional_modules}",
                source="config",
                rationale="optional modules requested as fallback candidates",
                confidence="medium",
            )
        )

    for item in policy.authority.values():
        entries.append(
            _trace_entry(
                f"{item.key} resolved to {item.value}",
                source=item.source,
                rationale=item.rationale,
                confidence=item.confidence,
                fallback_used=item.fallback_used,
            )
        )

    return entries


def build_policy_trace(*, config, facts: DetectedHostFacts, policy: DerivedSitePolicy, strict: bool) -> PolicyDecisionTrace:
    entries = _build_trace_entries(config=config, facts=facts, policy=policy, strict=strict)
    decisions = [entry.message for entry in entries]

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
    unresolved = [name for name in policy.requested_packages if name not in policy.packages]
    if unresolved:
        warnings.append(f"requested packages without validated external policy={unresolved}")

    return PolicyDecisionTrace(
        decisions=decisions,
        warnings=warnings,
        assumptions=sorted(set(assumptions)),
        entries=entries,
    )


def derive_policy_bundle(
    *,
    config,
    context: ExecutionContext,
    compiler,
    runtime_config,
    detected,
    linkage,
    specs: Dict[str, PackageSpec],
    strict: bool,
) -> PolicyDerivationBundle:
    facts = build_detected_host_facts(
        config=config,
        context=context,
        compiler=compiler,
        runtime_config=runtime_config,
        detected=detected,
        linkage=linkage,
    )
    policy = derive_site_policy(config=config, facts=facts, specs=specs)
    trace = build_policy_trace(config=config, facts=facts, policy=policy, strict=strict)
    return PolicyDerivationBundle(
        facts=facts,
        policy=policy,
        trace=trace,
    )
