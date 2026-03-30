from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    """Result of resolving a user/config-provided name against a registry.

    status:
      - 'canonical': requested name is already canonical (exists in registry keys)
      - 'alias': requested name is a declared alias for exactly one canonical name
      - 'ambiguous': requested name matches aliases from multiple packages
      - 'unknown': requested name matches neither canonicals nor aliases
    """

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
    metadata: Dict[str, object] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


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

