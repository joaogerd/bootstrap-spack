from __future__ import annotations

from typing import Dict, List, Optional, Set

from bootstrap.domain.models import (
    DetectedPackage,
    Hdf5ValidationDetails,
    MpiValidationDetails,
    NetcdfCValidationDetails,
    NetcdfFortranValidationDetails,
    PackageLinkage,
    ToolchainCheckResult,
)


def _get_pkg(packages: List[DetectedPackage], name: str) -> Optional[DetectedPackage]:
    for pkg in packages:
        if pkg.name == name:
            return pkg
    return None


def _valid(pkg: Optional[DetectedPackage]) -> bool:
    if not pkg:
        return False
    if not pkg.found:
        return False
    if not pkg.validation:
        return False
    return pkg.validation.valid


def _details(pkg: Optional[DetectedPackage]):
    if not pkg or not pkg.validation:
        return None
    return pkg.validation.details


def _prefix_from_pkg(pkg: Optional[DetectedPackage]) -> Optional[str]:
    if not pkg:
        return None
    if pkg.prefix:
        return pkg.prefix
    details = _details(pkg)
    if details is not None and hasattr(details, "prefix"):
        value = getattr(details, "prefix")
        if isinstance(value, str) and value:
            return value
    return None


def _parallel_netcdf_c(pkg: Optional[DetectedPackage]) -> bool:
    details = _details(pkg)
    return isinstance(details, NetcdfCValidationDetails) and details.parallel


def _parallel_hdf5(pkg: Optional[DetectedPackage]) -> bool:
    details = _details(pkg)
    return isinstance(details, Hdf5ValidationDetails) and details.parallel


def _mpi_family(pkg: Optional[DetectedPackage]) -> Optional[str]:
    details = _details(pkg)
    if isinstance(details, MpiValidationDetails):
        return details.family
    return None


def _infer_toolchain_tokens(*prefixes: Optional[str], mpi_family: Optional[str] = None) -> List[str]:
    tokens: Set[str] = set()

    if mpi_family:
        low_family = mpi_family.lower()
        if low_family in {"openmpi", "mpich", "intelmpi"}:
            tokens.add(low_family)

    for prefix in prefixes:
        if not prefix:
            continue

        low = prefix.lower()
        for token in ["gnu", "gcc", "openmpi", "mpich", "intel", "oneapi", "cray"]:
            if token in low:
                tokens.add(token)

    return sorted(tokens)


def _prefixes_compatible(linked_prefix: Optional[str], detected_prefix: Optional[str]) -> bool:
    if not linked_prefix or not detected_prefix:
        return True
    if linked_prefix == detected_prefix:
        return True
    if detected_prefix.startswith(linked_prefix.rstrip("/") + "/"):
        return True
    if linked_prefix.startswith(detected_prefix.rstrip("/") + "/"):
        return True
    return False


def check_toolchain(
    packages: List[DetectedPackage],
    linkage: Dict[str, PackageLinkage],
) -> ToolchainCheckResult:
    problems: List[str] = []
    warnings: List[str] = []

    mpi = _get_pkg(packages, "openmpi") or _get_pkg(packages, "mpich") or _get_pkg(packages, "mpi")
    hdf5 = _get_pkg(packages, "hdf5")
    ncc = _get_pkg(packages, "netcdf-c")
    ncf = _get_pkg(packages, "netcdf-fortran")

    mpi_valid = _valid(mpi)
    hdf5_valid = _valid(hdf5)
    ncc_valid = _valid(ncc)
    ncf_valid = _valid(ncf)

    mpi_prefix = _prefix_from_pkg(mpi)
    hdf5_prefix = _prefix_from_pkg(hdf5)
    ncc_prefix = _prefix_from_pkg(ncc)
    ncf_prefix = _prefix_from_pkg(ncf)

    tokens = _infer_toolchain_tokens(
        mpi_prefix,
        hdf5_prefix,
        ncc_prefix,
        ncf_prefix,
        mpi_family=_mpi_family(mpi),
    )

    if ncc_valid and _parallel_netcdf_c(ncc) and not mpi_valid:
        problems.append("NetCDF-C parallel sem MPI válido")

    if hdf5_valid and _parallel_hdf5(hdf5) and not mpi_valid:
        warnings.append("HDF5 paralelo sem MPI válido")

    if ncf_valid and not ncc_valid:
        problems.append("NetCDF-Fortran sem NetCDF-C válido")

    ncc_linkage = linkage.get("netcdf-c")
    if ncc_valid and ncc_linkage:
        if ncc_linkage.hdf5_prefix and hdf5_prefix and not _prefixes_compatible(ncc_linkage.hdf5_prefix, hdf5_prefix):
            problems.append(
                f"NetCDF-C linkado com HDF5 em {ncc_linkage.hdf5_prefix}, "
                f"mas HDF5 detectado em {hdf5_prefix}"
            )

        if ncc_linkage.mpi_prefix and mpi_prefix and not _prefixes_compatible(ncc_linkage.mpi_prefix, mpi_prefix):
            problems.append(
                f"NetCDF-C linkado com MPI em {ncc_linkage.mpi_prefix}, "
                f"mas MPI detectado em {mpi_prefix}"
            )

    ncf_linkage = linkage.get("netcdf-fortran")
    if ncf_valid and ncf_linkage:
        if ncf_linkage.netcdf_c_prefix and ncc_prefix and not _prefixes_compatible(ncf_linkage.netcdf_c_prefix, ncc_prefix):
            problems.append(
                f"NetCDF-Fortran linkado com NetCDF-C em {ncf_linkage.netcdf_c_prefix}, "
                f"mas NetCDF-C detectado em {ncc_prefix}"
            )

    if len([p for p in [mpi_prefix, hdf5_prefix, ncc_prefix, ncf_prefix] if p]) >= 2 and not tokens:
        warnings.append("Não foi possível inferir tokens de toolchain a partir dos prefixes")

    valid = len(problems) == 0

    reason = "toolchain consistente"
    if problems:
        reason = "; ".join(problems)
    elif warnings:
        reason = "sem problemas críticos; " + "; ".join(warnings)

    return ToolchainCheckResult(
        valid=valid,
        reason=reason,
        problems=problems,
        warnings=warnings,
        tokens=tokens,
    )
