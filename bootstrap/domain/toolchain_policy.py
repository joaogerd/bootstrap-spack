from __future__ import annotations

from typing import Dict, List, Optional, Set

from bootstrap.domain.models import DetectedPackage, PackageLinkage, ToolchainCheckResult


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


def _infer_toolchain_tokens(*prefixes: Optional[str]) -> List[str]:
    tokens: Set[str] = set()

    for prefix in prefixes:
        if not prefix:
            continue

        low = prefix.lower()

        for token in ["gnu", "gcc", "openmpi", "mpich", "intel", "oneapi", "cray"]:
            if token in low:
                tokens.add(token)

    return sorted(tokens)


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

    mpi_prefix = mpi.prefix if mpi else None
    hdf5_prefix = hdf5.prefix if hdf5 else None
    ncc_prefix = ncc.prefix if ncc else None
    ncf_prefix = ncf.prefix if ncf else None

    tokens = _infer_toolchain_tokens(
        mpi_prefix,
        hdf5_prefix,
        ncc_prefix,
        ncf_prefix,
    )

    ncc_meta = ncc.metadata if ncc else {}
    hdf5_meta = hdf5.metadata if hdf5 else {}

    if ncc_valid and ncc_meta.get("parallel") and not mpi_valid:
        problems.append("NetCDF-C parallel sem MPI válido")

    if hdf5_valid and hdf5_meta.get("parallel") and not mpi_valid:
        warnings.append("HDF5 paralelo sem MPI válido")

    if ncf_valid and not ncc_valid:
        problems.append("NetCDF-Fortran sem NetCDF-C válido")

    ncc_linkage = linkage.get("netcdf-c")
    if ncc_valid and ncc_linkage:
        if ncc_linkage.hdf5_prefix and hdf5_prefix and ncc_linkage.hdf5_prefix != hdf5_prefix:
            problems.append(
                f"NetCDF-C linkado com HDF5 em {ncc_linkage.hdf5_prefix}, "
                f"mas HDF5 detectado em {hdf5_prefix}"
            )

        if ncc_linkage.mpi_prefix and mpi_prefix and ncc_linkage.mpi_prefix != mpi_prefix:
            problems.append(
                f"NetCDF-C linkado com MPI em {ncc_linkage.mpi_prefix}, "
                f"mas MPI detectado em {mpi_prefix}"
            )

    ncf_linkage = linkage.get("netcdf-fortran")
    if ncf_valid and ncf_linkage:
        if ncf_linkage.netcdf_c_prefix and ncc_prefix and ncf_linkage.netcdf_c_prefix != ncc_prefix:
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
