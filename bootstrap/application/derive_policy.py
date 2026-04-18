from __future__ import annotations

from typing import Dict, List, Optional

from bootstrap.domain.models import (
    DerivedSitePolicy,
    DetectedHostFacts,
    DetectedPackage,
    ExecutionContext,
    PackageSpec,
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
    if facts.module_system:
        entries.append(
            _trace_entry(
                f"module system set to {facts.module_system}",
                source="config",
                rationale="module backend declared in site configuration",
            )
        )
    if facts.compiler is not None:
        entries.append(
            _trace_entry(
                f"compiler entry derived as {facts.compiler.spec}",
                source="detection",
                rationale="compiler entry inferred from active host toolchain",
                confidence="medium" if facts.platform_family in {"cray", "cluster"} else "high",
            )
        )
    if facts.runtime is not None:
        entries.extend(
            [
                _trace_entry(
                    f"runtime config derived for site {config.site.name or 'unspecified'}",
                    source="detection",
                    rationale="site runtime values inferred from host filesystem and environment",
                    confidence="medium",
                ),
                _trace_entry(
                    f"build_jobs resolved to {facts.runtime.build_jobs}",
                    source="policy",
                    rationale="build jobs derived from detected host capacity and site limits",
                    confidence="medium",
                    fallback_used="site.build_jobs" if facts.runtime.build_jobs == config.site.build_jobs else None,
                ),
                _trace_entry(
                    f"install_tree_root resolved to {facts.runtime.install_tree_root}",
                    source="policy",
                    rationale="install tree root derived from detected runtime policy",
                    confidence="medium",
                ),
                _trace_entry(
                    f"build_stage resolved to {facts.runtime.build_stage}",
                    source="policy",
                    rationale="build stage derived from detected scratch and temporary paths",
                    confidence="medium",
                ),
                _trace_entry(
                    f"test_stage resolved to {facts.runtime.test_stage}",
                    source="policy",
                    rationale="test stage derived from detected scratch and temporary paths",
                    confidence="medium",
                ),
            ]
        )
    if policy.providers:
        for virtual, provider_list in policy.providers.items():
            entries.append(
                _trace_entry(
                    f"provider policy for {virtual} set to {provider_list}",
                    source="policy",
                    rationale="provider chosen from validated MPI implementations using current provider selection rule",
                    confidence="medium",
                    fallback_used="preference order: openmpi -> mpich",
                )
            )
    else:
        entries.append(
            _trace_entry(
                "no virtual providers inferred",
                source="policy",
                rationale="no validated package matched the current provider derivation rules",
                confidence="heuristic",
            )
        )
    if config.template.enabled:
        entries.append(
            _trace_entry(
                f"template policy enabled for {config.template.name or 'unnamed-template'}",
                source="config",
                rationale="template section is enabled in bootstrap configuration",
            )
        )
    if policy.common_modules_enabled:
        entries.append(
            _trace_entry(
                f"common modules enabled={policy.common_modules_enabled}",
                source="policy",
                rationale="common module policy derived from site module backend",
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
