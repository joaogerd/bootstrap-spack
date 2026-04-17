from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional


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
    | CompileCheckDetails
)


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
    strict_validation: bool
    platform: Optional[str] = None


@dataclass(frozen=True)
class BootstrapConfig:
    platform: Optional[str]
    output_dir: str
    strict_validation: bool
    modules_to_load: List[str]
    modules_optional: List[str]
    external_packages: List[str]


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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
