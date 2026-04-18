from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Literal, Optional

SUPPORTED_SITE_LAYOUTS = ("spack-stack",)

PolicySource = Literal["config", "detection", "policy", "override", "default", "legacy-compat"]
PolicyConfidence = Literal["high", "medium", "low", "heuristic"]
PolicyFieldKind = Literal["factual", "derived", "institutional", "template"]

AUTHORITY_PRECEDENCE: Dict[str, int] = {
    "legacy-compat": 0,
    "default": 100,
    "policy": 200,
    "detection": 300,
    "config": 400,
    "override": 500,
}


@dataclass(frozen=True)
class FieldAuthorityRule:
    key: str
    field_kind: PolicyFieldKind
    preferred_source: PolicySource
    allowed_sources: List[PolicySource]
    override_allowed: bool
    description: str


FIELD_AUTHORITY_RULES: Dict[str, FieldAuthorityRule] = {
    "module_system": FieldAuthorityRule(
        key="module_system",
        field_kind="institutional",
        preferred_source="config",
        allowed_sources=["config", "override", "legacy-compat"],
        override_allowed=False,
        description="Module backend is an institutional site choice declared by configuration.",
    ),
    "compiler": FieldAuthorityRule(
        key="compiler",
        field_kind="factual",
        preferred_source="detection",
        allowed_sources=["detection", "config", "override", "legacy-compat"],
        override_allowed=False,
        description="Compiler policy should be anchored in observed host toolchain evidence.",
    ),
    "runtime.build_jobs": FieldAuthorityRule(
        key="runtime.build_jobs",
        field_kind="derived",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Build parallelism is derived from host/runtime policy but may be explicitly overridden.",
    ),
    "runtime.install_tree_root": FieldAuthorityRule(
        key="runtime.install_tree_root",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Install tree location is a site policy decision that may be explicitly overridden.",
    ),
    "runtime.build_stage": FieldAuthorityRule(
        key="runtime.build_stage",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Build stage paths are runtime policy decisions that may be explicitly overridden.",
    ),
    "runtime.test_stage": FieldAuthorityRule(
        key="runtime.test_stage",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Test stage paths are runtime policy decisions that may be explicitly overridden.",
    ),
    "runtime.source_cache": FieldAuthorityRule(
        key="runtime.source_cache",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Source cache location is a runtime policy decision that may be explicitly overridden.",
    ),
    "runtime.misc_cache": FieldAuthorityRule(
        key="runtime.misc_cache",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="Misc cache location is a runtime policy decision that may be explicitly overridden.",
    ),
    "providers.mpi": FieldAuthorityRule(
        key="providers.mpi",
        field_kind="derived",
        preferred_source="policy",
        allowed_sources=["policy", "override", "config", "default", "legacy-compat"],
        override_allowed=True,
        description="MPI provider is derived from validated packages and may be explicitly overridden by site policy.",
    ),
    "common_modules_enabled": FieldAuthorityRule(
        key="common_modules_enabled",
        field_kind="institutional",
        preferred_source="policy",
        allowed_sources=["policy", "config", "legacy-compat"],
        override_allowed=False,
        description="Common module enablement follows the selected site module backend.",
    ),
    "template.enabled": FieldAuthorityRule(
        key="template.enabled",
        field_kind="template",
        preferred_source="config",
        allowed_sources=["config", "override", "legacy-compat"],
        override_allowed=False,
        description="Template enablement is driven by explicit template configuration.",
    ),
}


@dataclass(frozen=True)
class CompileCheckDetails:
    ok: bool
    cmd: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class MpiValidationDetails:
    prefix: Optional[str]
    family: str
    version: Optional[str]
    version_line: str
    mpi_wrapper: Optional[str]
    wrapper_show: str
    compile: Optional[CompileCheckDetails] = None


@dataclass(frozen=True)
class Hdf5ValidationDetails:
    prefix: Optional[str]
    parallel: bool
    show: str
    config_head: str
    version: Optional[str]
    compile: Optional[CompileCheckDetails] = None


@dataclass(frozen=True)
class NetcdfCValidationDetails:
    prefix: Optional[str]
    version_line: str
    version: Optional[str]
    cflags: str
    libs: str
    parallel: bool
    compiler_used: Optional[str]
    compile: Optional[CompileCheckDetails] = None


@dataclass(frozen=True)
class NetcdfFortranValidationDetails:
    prefix: Optional[str]
    version_line: str
    version: Optional[str]
    fflags: str
    flibs: str
    fc_used: Optional[str]
    compile: Optional[CompileCheckDetails] = None


ValidationDetails = (
    MpiValidationDetails
    | Hdf5ValidationDetails
    | NetcdfCValidationDetails
    | NetcdfFortranValidationDetails
)


@dataclass(frozen=True)
class SitePolicyRuntimeOverrides:
    build_jobs: Optional[int] = None
    install_tree_root: Optional[str] = None
    build_stage: List[str] = field(default_factory=list)
    test_stage: Optional[str] = None
    source_cache: Optional[str] = None
    misc_cache: Optional[str] = None


@dataclass(frozen=True)
class SitePolicyOverrides:
    mpi_provider: List[str] = field(default_factory=list)
    runtime: SitePolicyRuntimeOverrides = field(default_factory=SitePolicyRuntimeOverrides)


@dataclass(frozen=True)
class SiteConfig:
    name: Optional[str] = None
    layout: str = "spack-stack"
    module_system: str = "lmod"
    build_jobs: int = 8
    core_compilers: List[str] = field(default_factory=list)
    policy_overrides: SitePolicyOverrides = field(default_factory=SitePolicyOverrides)

    @property
    def enabled(self) -> bool:
        return bool(self.name)


@dataclass(frozen=True)
class TemplateConfig:
    name: Optional[str] = None
    specs: List[str] = field(default_factory=list)
    compiler: Optional[str] = None

    @property
    def enabled(self) -> bool:
        return bool(self.name or self.specs)


@dataclass(frozen=True)
class CompilerEntry:
    spec: str
    cc: str
    cxx: str
    f77: str
    fc: str
    operating_system: str
    target: str
    modules: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SiteRuntimeConfig:
    build_jobs: int
    install_tree_root: str
    build_stage: List[str]
    test_stage: str
    source_cache: str
    misc_cache: str


@dataclass(frozen=True)
class LayeredSpackStackArtifacts:
    common_packages_yaml: str
    common_modules_yaml: str
    site_packages_yaml: str
    site_compilers_yaml: str
    site_modules_yaml: str
    site_config_yaml: str
    template_spack_yaml: Optional[str] = None


@dataclass(frozen=True)
class PackageDefinition:
    name: str
    aliases: List[str]
    tools: List[str]
    validation_type: str
    family: str
    depends_on_hdf5: bool = False
    depends_on_netcdf_c: bool = False
    depends_on_mpi_optional: bool = False
    parallel_optional: bool = False


@dataclass(frozen=True)
class PackageNameResolution:
    requested: str
    normalized: str
    canonical: Optional[str]
    status: str
    candidates: List[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.canonical is not None and self.status in {"canonical", "alias"}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str
    details: Optional[ValidationDetails] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def metadata(self) -> Dict[str, object]:
        if self.details is None:
            return {}
        if is_dataclass(self.details):
            return asdict(self.details)
        return {}


@dataclass(frozen=True)
class DetectedPackage:
    name: str
    found: bool
    prefix: Optional[str] = None
    method: Optional[str] = None
    tool_paths: Dict[str, str] = field(default_factory=dict)
    validation: Optional[ValidationResult] = None
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PackageLinkage:
    linked_paths: Dict[str, str] = field(default_factory=dict)
    hdf5_prefix: Optional[str] = None
    mpi_prefix: Optional[str] = None
    netcdf_c_prefix: Optional[str] = None


@dataclass(frozen=True)
class PackageSpec:
    package: str
    spec: str
    prefix: str
    confidence: str = "high"
    assumptions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ToolchainCheckResult:
    valid: bool
    reason: str
    problems: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tokens: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionContext:
    base_env: Dict[str, str]
    loaded_modules: List[str]
    optional_modules: List[str] = field(default_factory=list)
    strict_validation: bool = False
    platform: Optional[str] = None


@dataclass(frozen=True)
class BootstrapConfig:
    platform: Optional[str]
    output_dir: str
    strict_validation: bool
    modules_to_load: List[str]
    modules_optional: List[str]
    external_packages: List[str]
    site: SiteConfig = field(default_factory=SiteConfig)
    template: TemplateConfig = field(default_factory=TemplateConfig)


@dataclass(frozen=True)
class DetectedHostFacts:
    platform_family: Optional[str]
    module_system: Optional[str]
    loaded_modules: List[str]
    optional_modules: List[str]
    compiler: Optional[CompilerEntry]
    packages: Dict[str, DetectedPackage]
    linkage: Dict[str, PackageLinkage]
    runtime: Optional[SiteRuntimeConfig]


@dataclass(frozen=True)
class PolicyAuthority:
    key: str
    value: str
    source: PolicySource
    rationale: str
    confidence: PolicyConfidence = "high"
    precedence_rank: int = 0
    fallback_used: Optional[str] = None
    overridden_by: Optional[str] = None
    supersedes_source: Optional[PolicySource] = None
    legacy_compat_used: bool = False
    field_kind: Optional[PolicyFieldKind] = None
    preferred_source: Optional[PolicySource] = None
    allowed_sources: List[PolicySource] = field(default_factory=list)
    override_allowed: bool = False
    rule_description: Optional[str] = None


@dataclass(frozen=True)
class DerivedSitePolicy:
    site: SiteConfig
    template: TemplateConfig
    runtime: Optional[SiteRuntimeConfig]
    compiler: Optional[CompilerEntry]
    requested_packages: List[str]
    packages: Dict[str, PackageSpec]
    providers: Dict[str, List[str]] = field(default_factory=dict)
    common_modules_enabled: List[str] = field(default_factory=list)
    authority: Dict[str, PolicyAuthority] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyTraceEntry:
    message: str
    source: PolicySource
    rationale: str
    confidence: PolicyConfidence = "high"
    fallback_used: Optional[str] = None


@dataclass(frozen=True)
class PolicyDecisionTrace:
    decisions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    entries: List[PolicyTraceEntry] = field(default_factory=list)


@dataclass(frozen=True)
class PolicyDerivationBundle:
    facts: DetectedHostFacts
    policy: DerivedSitePolicy
    trace: PolicyDecisionTrace


@dataclass(frozen=True)
class BootstrapResult:
    config_path: str
    platform: Optional[str]
    modules: List[str]
    packages: List[str]
    strict: bool
    dry_run: bool
    detected: Dict[str, DetectedPackage]
    linkage: Dict[str, PackageLinkage]
    specs: Dict[str, PackageSpec]
    toolchain: ToolchainCheckResult
    output_report: Optional[str]
    output_yaml: Optional[str]
    facts: Optional[DetectedHostFacts] = None
    policy: Optional[DerivedSitePolicy] = None
    trace: Optional[PolicyDecisionTrace] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
