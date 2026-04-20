from __future__ import annotations

from typing import Dict, List, Optional

from bootstrap.domain.models import (
    AUTHORITY_PRECEDENCE,
    FIELD_AUTHORITY_RULES,
    DerivedSitePolicy,
    DetectedHostFacts,
    DetectedPackage,
    ExecutionContext,
    ExternalPackagePolicy,
    ModulePolicy,
    PackageSpec,
    PolicyAuthority,
    PolicyDecisionTrace,
    PolicyDerivationBundle,
    PolicySource,
    PolicyTraceEntry,
    ProviderPolicy,
    RuntimePolicy,
    SiteRuntimeConfig,
    TemplatePolicy,
)
from bootstrap.infrastructure.platform.detector import detect_platform_facts


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
        platform_facts=detect_platform_facts(),
    )



def _authority(
    *,
    key: str,
    value: str,
    source: PolicySource,
    rationale: str,
    confidence: str = "high",
    fallback_used: Optional[str] = None,
    overridden_by: Optional[str] = None,
    supersedes_source: Optional[PolicySource] = None,
    legacy_compat_used: bool = False,
) -> PolicyAuthority:
    rule = FIELD_AUTHORITY_RULES.get(key)
    return PolicyAuthority(
        key=key,
        value=value,
        source=source,
        rationale=rationale,
        confidence=confidence,
        precedence_rank=AUTHORITY_PRECEDENCE[source],
        fallback_used=fallback_used,
        overridden_by=overridden_by,
        supersedes_source=supersedes_source,
        legacy_compat_used=legacy_compat_used,
        field_kind=rule.field_kind if rule else None,
        preferred_source=rule.preferred_source if rule else None,
        allowed_sources=list(rule.allowed_sources) if rule else [],
        override_allowed=rule.override_allowed if rule else False,
        rule_description=rule.description if rule else None,
    )



def _apply_runtime_overrides(config, runtime: Optional[SiteRuntimeConfig]) -> Optional[SiteRuntimeConfig]:
    overrides = config.site.policy_overrides.runtime
    if runtime is None:
        return None

    return SiteRuntimeConfig(
        build_jobs=overrides.build_jobs or runtime.build_jobs,
        install_tree_root=overrides.install_tree_root or runtime.install_tree_root,
        build_stage=list(overrides.build_stage) if overrides.build_stage else list(runtime.build_stage),
        test_stage=overrides.test_stage or runtime.test_stage,
        source_cache=overrides.source_cache or runtime.source_cache,
        misc_cache=overrides.misc_cache or runtime.misc_cache,
    )



def _apply_provider_overrides(config, providers: Dict[str, list[str]]) -> Dict[str, list[str]]:
    updated = dict(providers)
    override_mpi = list(config.site.policy_overrides.mpi_provider)
    if override_mpi:
        updated["mpi"] = override_mpi
    return updated



def _derive_policy_operating_system(config, facts: DetectedHostFacts) -> tuple[Optional[str], PolicySource]:
    override_value = config.site.policy_overrides.platform.operating_system
    if override_value:
        return override_value, "override"
    if facts.platform_facts is not None:
        return facts.platform_facts.operating_system, "detection"
    if facts.compiler is not None and facts.compiler.operating_system:
        return facts.compiler.operating_system, "legacy-compat"
    return None, "default"



def _derive_policy_target(config, facts: DetectedHostFacts) -> tuple[Optional[str], PolicySource]:
    override_value = config.site.policy_overrides.platform.target
    if override_value:
        return override_value, "override"
    if facts.platform_facts is not None:
        return facts.platform_facts.target, "detection"
    if facts.compiler is not None and facts.compiler.target:
        return facts.compiler.target, "legacy-compat"
    return None, "default"



def _build_external_package_policy(
    requested_packages: List[str],
    specs: Dict[str, PackageSpec],
) -> Dict[str, ExternalPackagePolicy]:
    policies: Dict[str, ExternalPackagePolicy] = {}

    for name in requested_packages:
        spec = specs.get(name)
        if spec is not None:
            policies[name] = ExternalPackagePolicy(
                package=name,
                requested=True,
                spec=spec,
                buildable=False,
                source="policy",
                status="validated-external",
            )
        else:
            policies[name] = ExternalPackagePolicy(
                package=name,
                requested=True,
                spec=None,
                buildable=True,
                source="policy",
                status="unresolved",
            )

    return policies



def _build_provider_policy(providers: Dict[str, list[str]]) -> ProviderPolicy:
    return ProviderPolicy(providers=dict(providers))



def _build_module_policy(config, compiler, common_modules_enabled: List[str]) -> ModulePolicy:
    site_core_compilers = list(config.site.core_compilers)
    if not site_core_compilers and compiler is not None:
        site_core_compilers = [compiler.spec]

    return ModulePolicy(
        backend=config.site.module_system if config.site.enabled else None,
        common_enabled=list(common_modules_enabled),
        site_core_compilers=site_core_compilers,
    )



def _build_runtime_policy(config, runtime: Optional[SiteRuntimeConfig]) -> Optional[RuntimePolicy]:
    if runtime is None:
        return None

    overrides = config.site.policy_overrides.runtime
    overridden_fields: List[str] = []
    if overrides.build_jobs is not None:
        overridden_fields.append("runtime.build_jobs")
    if overrides.install_tree_root:
        overridden_fields.append("runtime.install_tree_root")
    if overrides.build_stage:
        overridden_fields.append("runtime.build_stage")
    if overrides.test_stage:
        overridden_fields.append("runtime.test_stage")
    if overrides.source_cache:
        overridden_fields.append("runtime.source_cache")
    if overrides.misc_cache:
        overridden_fields.append("runtime.misc_cache")

    return RuntimePolicy(
        config=runtime,
        overridden_fields=overridden_fields,
    )



def _build_template_policy(config) -> TemplatePolicy:
    return TemplatePolicy(
        enabled=config.template.enabled,
        name=config.template.name,
        specs=list(config.template.specs),
        compiler=config.template.compiler,
    )



def _build_policy_authority(
    *,
    config,
    facts: DetectedHostFacts,
    providers: Dict[str, list[str]],
    runtime: Optional[SiteRuntimeConfig],
    policy_operating_system: Optional[str],
    policy_target: Optional[str],
    policy_operating_system_source: PolicySource,
    policy_target_source: PolicySource,
) -> Dict[str, PolicyAuthority]:
    authority: Dict[str, PolicyAuthority] = {}
    runtime_overrides = config.site.policy_overrides.runtime

    if facts.module_system:
        authority["module_system"] = _authority(
            key="module_system",
            value=facts.module_system,
            source="config",
            rationale="module backend declared in site configuration",
            confidence="high",
        )

    if facts.compiler is not None:
        authority["compiler"] = _authority(
            key="compiler",
            value=facts.compiler.spec,
            source="detection",
            rationale="compiler entry inferred from active host toolchain",
            confidence="medium" if facts.platform_family in {"cray", "cluster"} else "high",
        )

    if policy_operating_system:
        authority["platform.operating_system"] = _authority(
            key="platform.operating_system",
            value=policy_operating_system,
            source=policy_operating_system_source,
            rationale=(
                "operating system forced by site.policy_overrides.platform.operating_system"
                if policy_operating_system_source == "override"
                else "derived from platform detector compatible with Spack operating-system normalization"
            ),
            confidence="high",
            overridden_by=(
                "site.policy_overrides.platform.operating_system"
                if policy_operating_system_source == "override"
                else None
            ),
            supersedes_source="detection" if policy_operating_system_source == "override" else None,
            legacy_compat_used=policy_operating_system_source == "legacy-compat",
            fallback_used=(
                "compiler.operating_system"
                if policy_operating_system_source == "legacy-compat"
                else None
            ),
        )

    if policy_target:
        authority["platform.target"] = _authority(
            key="platform.target",
            value=policy_target,
            source=policy_target_source,
            rationale=(
                "target forced by site.policy_overrides.platform.target"
                if policy_target_source == "override"
                else "derived from platform detector compatible with Spack target detection"
            ),
            confidence="high",
            overridden_by=(
                "site.policy_overrides.platform.target"
                if policy_target_source == "override"
                else None
            ),
            supersedes_source="detection" if policy_target_source == "override" else None,
            legacy_compat_used=policy_target_source == "legacy-compat",
            fallback_used="compiler.target" if policy_target_source == "legacy-compat" else None,
        )

    if runtime is not None:
        authority["runtime.build_jobs"] = _authority(
            key="runtime.build_jobs",
            value=str(runtime.build_jobs),
            source="override" if runtime_overrides.build_jobs is not None else "policy",
            rationale=(
                "build jobs forced by site.policy_overrides.runtime.build_jobs"
                if runtime_overrides.build_jobs is not None
                else "build jobs derived from detected host capacity and site limits"
            ),
            confidence="high" if runtime_overrides.build_jobs is not None else "medium",
            fallback_used="site.build_jobs" if runtime_overrides.build_jobs is None and facts.runtime and facts.runtime.build_jobs == config.site.build_jobs else None,
            overridden_by="site.policy_overrides.runtime.build_jobs" if runtime_overrides.build_jobs is not None else None,
            supersedes_source="policy" if runtime_overrides.build_jobs is not None else None,
        )
        authority["runtime.install_tree_root"] = _authority(
            key="runtime.install_tree_root",
            value=runtime.install_tree_root,
            source="override" if runtime_overrides.install_tree_root else "policy",
            rationale=(
                "install tree root forced by site.policy_overrides.runtime.install_tree_root"
                if runtime_overrides.install_tree_root
                else "install tree root derived from detected runtime policy"
            ),
            confidence="high" if runtime_overrides.install_tree_root else "medium",
            overridden_by="site.policy_overrides.runtime.install_tree_root" if runtime_overrides.install_tree_root else None,
            supersedes_source="policy" if runtime_overrides.install_tree_root else None,
        )
        authority["runtime.build_stage"] = _authority(
            key="runtime.build_stage",
            value=str(runtime.build_stage),
            source="override" if runtime_overrides.build_stage else "policy",
            rationale=(
                "build stage forced by site.policy_overrides.runtime.build_stage"
                if runtime_overrides.build_stage
                else "build stage derived from detected scratch and temporary paths"
            ),
            confidence="high" if runtime_overrides.build_stage else "medium",
            overridden_by="site.policy_overrides.runtime.build_stage" if runtime_overrides.build_stage else None,
            supersedes_source="policy" if runtime_overrides.build_stage else None,
        )
        authority["runtime.test_stage"] = _authority(
            key="runtime.test_stage",
            value=runtime.test_stage,
            source="override" if runtime_overrides.test_stage else "policy",
            rationale=(
                "test stage forced by site.policy_overrides.runtime.test_stage"
                if runtime_overrides.test_stage
                else "test stage derived from detected scratch and temporary paths"
            ),
            confidence="high" if runtime_overrides.test_stage else "medium",
            overridden_by="site.policy_overrides.runtime.test_stage" if runtime_overrides.test_stage else None,
            supersedes_source="policy" if runtime_overrides.test_stage else None,
        )
        authority["runtime.source_cache"] = _authority(
            key="runtime.source_cache",
            value=runtime.source_cache,
            source="override" if runtime_overrides.source_cache else "policy",
            rationale=(
                "source cache forced by site.policy_overrides.runtime.source_cache"
                if runtime_overrides.source_cache
                else "source cache derived from detected runtime policy"
            ),
            confidence="high" if runtime_overrides.source_cache else "medium",
            overridden_by="site.policy_overrides.runtime.source_cache" if runtime_overrides.source_cache else None,
            supersedes_source="policy" if runtime_overrides.source_cache else None,
        )
        authority["runtime.misc_cache"] = _authority(
            key="runtime.misc_cache",
            value=runtime.misc_cache,
            source="override" if runtime_overrides.misc_cache else "policy",
            rationale=(
                "misc cache forced by site.policy_overrides.runtime.misc_cache"
                if runtime_overrides.misc_cache
                else "misc cache derived from detected runtime policy"
            ),
            confidence="high" if runtime_overrides.misc_cache else "medium",
            overridden_by="site.policy_overrides.runtime.misc_cache" if runtime_overrides.misc_cache else None,
            supersedes_source="policy" if runtime_overrides.misc_cache else None,
        )

    if "mpi" in providers:
        override_mpi = list(config.site.policy_overrides.mpi_provider)
        authority["providers.mpi"] = _authority(
            key="providers.mpi",
            value=str(providers["mpi"]),
            source="override" if override_mpi else "policy",
            rationale=(
                "MPI provider forced by site.policy_overrides.providers.mpi"
                if override_mpi
                else "provider chosen from validated MPI implementations using current provider selection rule"
            ),
            confidence="high" if override_mpi else "medium",
            fallback_used=None if override_mpi else "preference order: openmpi -> mpich",
            overridden_by="site.policy_overrides.providers.mpi" if override_mpi else None,
            supersedes_source="policy" if override_mpi else None,
        )

    common_modules_enabled = [config.site.module_system] if config.site.enabled else []
    if common_modules_enabled:
        authority["common_modules_enabled"] = _authority(
            key="common_modules_enabled",
            value=str(common_modules_enabled),
            source="policy",
            rationale="common module policy derived from site module backend",
            confidence="high",
        )

    if config.template.enabled:
        authority["template.enabled"] = _authority(
            key="template.enabled",
            value=config.template.name or "unnamed-template",
            source="config",
            rationale="template section is enabled in bootstrap configuration",
            confidence="high",
        )

    return authority



def derive_site_policy(*, config, facts: DetectedHostFacts, specs: Dict[str, PackageSpec]) -> DerivedSitePolicy:
    common_modules_enabled = [config.site.module_system] if config.site.enabled else []
    providers = _apply_provider_overrides(config, derive_policy_providers(facts.packages))
    runtime = _apply_runtime_overrides(config, facts.runtime)
    policy_operating_system, policy_operating_system_source = _derive_policy_operating_system(config, facts)
    policy_target, policy_target_source = _derive_policy_target(config, facts)
    authority = _build_policy_authority(
        config=config,
        facts=facts,
        providers=providers,
        runtime=runtime,
        policy_operating_system=policy_operating_system,
        policy_target=policy_target,
        policy_operating_system_source=policy_operating_system_source,
        policy_target_source=policy_target_source,
    )
    external_packages = _build_external_package_policy(list(config.external_packages), specs)
    provider_policy = _build_provider_policy(providers)
    module_policy = _build_module_policy(config, facts.compiler, common_modules_enabled)
    runtime_policy = _build_runtime_policy(config, runtime)
    template_policy = _build_template_policy(config)

    return DerivedSitePolicy(
        site=config.site,
        template=config.template,
        runtime=runtime,
        compiler=facts.compiler,
        requested_packages=list(config.external_packages),
        packages=dict(specs),
        providers=providers,
        common_modules_enabled=common_modules_enabled,
        external_packages=external_packages,
        provider_policy=provider_policy,
        module_policy=module_policy,
        runtime_policy=runtime_policy,
        template_policy=template_policy,
        authority=authority,
        policy_platform=facts.platform_facts.platform if facts.platform_facts is not None else None,
        policy_operating_system=policy_operating_system,
        policy_target=policy_target,
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

    if facts.platform_facts is not None:
        entries.append(
            _trace_entry(
                (
                    "detected platform facts="
                    f"{facts.platform_facts.platform}-"
                    f"{facts.platform_facts.operating_system}-"
                    f"{facts.platform_facts.target}"
                ),
                source="detection",
                rationale="platform facts detected independently from compiler metadata",
                confidence="high",
            )
        )

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



def _build_authority_warnings(policy: DerivedSitePolicy) -> List[str]:
    warnings: List[str] = []

    for key, authority in policy.authority.items():
        if authority.allowed_sources and authority.source not in authority.allowed_sources:
            warnings.append(f"field '{key}' resolved from unexpected source '{authority.source}'")

        if authority.source == "override" and not authority.override_allowed:
            warnings.append(f"field '{key}' used override where override is not supported")

        if authority.legacy_compat_used:
            warnings.append(f"field '{key}' depended on legacy compatibility behavior")

        if authority.source != authority.preferred_source and authority.source not in {"override", "legacy-compat"}:
            warnings.append(
                f"field '{key}' resolved from '{authority.source}' instead of preferred '{authority.preferred_source}'"
            )

    return warnings



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
    unresolved = [name for name, package_policy in policy.external_packages.items() if package_policy.status == "unresolved"]
    if unresolved:
        warnings.append(f"requested packages without validated external policy={unresolved}")

    warnings.extend(_build_authority_warnings(policy))

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
