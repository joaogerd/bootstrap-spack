from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from bootstrap.domain.models import (
    DetectedPackage,
    Hdf5ValidationDetails,
    MpiValidationDetails,
    NetcdfCValidationDetails,
    NetcdfFortranValidationDetails,
    PackageLinkage,
    PackageSpec,
)
from bootstrap.shared.exceptions import SpecBuildError


def _details(pkg: DetectedPackage):
    return pkg.validation.details if pkg.validation else None


def _version(pkg: DetectedPackage) -> Optional[str]:
    details = _details(pkg)
    if details is not None and hasattr(details, "version"):
        value = getattr(details, "version")
        return value if isinstance(value, str) and value else None
    value = pkg.metadata.get("version")
    return value if isinstance(value, str) and value else None


def _prefix(pkg: DetectedPackage) -> Optional[str]:
    if pkg.prefix:
        return pkg.prefix
    details = _details(pkg)
    if details is not None and hasattr(details, "prefix"):
        value = getattr(details, "prefix")
        return value if isinstance(value, str) and value else None
    value = pkg.metadata.get("prefix")
    return value if isinstance(value, str) and value else None


def _mpi_family(pkg: DetectedPackage) -> str:
    details = _details(pkg)
    if isinstance(details, MpiValidationDetails):
        return details.family.lower()
    value = pkg.metadata.get("family")
    return str(value).lower() if value is not None else ""


def _hdf5_parallel(pkg: DetectedPackage) -> bool:
    details = _details(pkg)
    if isinstance(details, Hdf5ValidationDetails):
        return details.parallel
    return bool(pkg.metadata.get("parallel"))


def _netcdf_c_parallel(pkg: DetectedPackage) -> bool:
    details = _details(pkg)
    if isinstance(details, NetcdfCValidationDetails):
        return details.parallel
    return bool(pkg.metadata.get("parallel"))


def _base_spec(pkg: DetectedPackage) -> str:
    version = _version(pkg)
    spec = pkg.name
    if version:
        spec += f"@{version}"
    return spec


def _mpi_name_for_spec(pkg: DetectedPackage) -> str:
    family = _mpi_family(pkg)
    if pkg.name == "mpich" or family == "mpich":
        return "mpich"
    if pkg.name == "openmpi" or family == "openmpi":
        return "openmpi"
    if family == "intelmpi":
        return "intel-oneapi-mpi"
    return pkg.name


def _mpi_dep_spec(pkg: DetectedPackage) -> str:
    name = _mpi_name_for_spec(pkg)
    version = _version(pkg)
    return name + (f"@{version}" if version else "")


def _build_mpi_spec(pkg: DetectedPackage) -> Tuple[str, str, List[str]]:
    family = _mpi_family(pkg)
    confidence = "high" if family in {"openmpi", "mpich", "intelmpi"} else "medium"
    assumptions: List[str] = []
    if family not in {"openmpi", "mpich", "intelmpi"}:
        assumptions.append("MPI family inferred with limited confidence")
    return _mpi_dep_spec(pkg), confidence, assumptions


def _build_hdf5_spec(
    pkg: DetectedPackage,
    detected: Dict[str, DetectedPackage],
) -> Tuple[str, str, List[str]]:
    spec = _base_spec(pkg)
    assumptions: List[str] = []
    confidence = "high"

    if _hdf5_parallel(pkg):
        mpi_pkg = detected.get("openmpi") or detected.get("mpich") or detected.get("mpi")
        if mpi_pkg and mpi_pkg.found and mpi_pkg.validation and mpi_pkg.validation.valid:
            spec += f" ^{_mpi_dep_spec(mpi_pkg)}"
            assumptions.append("parallel HDF5 dependency on MPI inferred from wrapper/config output")
            confidence = "medium"
        else:
            assumptions.append("parallel HDF5 detected without a validated MPI dependency in generated spec")
            confidence = "low"

    return spec, confidence, assumptions


def _build_netcdf_c_spec(
    pkg: DetectedPackage,
    linkage: PackageLinkage,
    detected: Dict[str, DetectedPackage],
) -> Tuple[str, str, List[str]]:
    spec = _base_spec(pkg)
    assumptions: List[str] = []
    confidence = "high"

    mpi_pkg = detected.get("openmpi") or detected.get("mpich") or detected.get("mpi")
    if linkage.mpi_prefix and mpi_pkg and mpi_pkg.found and mpi_pkg.validation and mpi_pkg.validation.valid:
        spec += f" ^{_mpi_dep_spec(mpi_pkg)}"
        assumptions.append("MPI dependency inferred from dynamic linkage")
        confidence = "medium"

    hdf5_pkg = detected.get("hdf5")
    if linkage.hdf5_prefix and hdf5_pkg and hdf5_pkg.found and hdf5_pkg.validation and hdf5_pkg.validation.valid:
        hdf5_version = _version(hdf5_pkg)
        hdf5_dep = "hdf5" + (f"@{hdf5_version}" if hdf5_version else "")
        spec += f" ^{hdf5_dep}"
        assumptions.append("HDF5 dependency inferred from dynamic linkage")
        confidence = "medium"

    if _netcdf_c_parallel(pkg):
        assumptions.append("NetCDF-C parallel capability inferred from nc-config")
        confidence = "medium"

    return spec, confidence, assumptions


def _build_netcdf_fortran_spec(
    pkg: DetectedPackage,
    linkage: PackageLinkage,
    detected: Dict[str, DetectedPackage],
) -> Tuple[str, str, List[str]]:
    spec = _base_spec(pkg)
    assumptions: List[str] = []
    confidence = "high"

    ncc_pkg = detected.get("netcdf-c")
    if ncc_pkg and ncc_pkg.found and ncc_pkg.validation and ncc_pkg.validation.valid:
        ncc_version = _version(ncc_pkg)
        ncc_dep = "netcdf-c" + (f"@{ncc_version}" if ncc_version else "")
        spec += f" ^{ncc_dep}"
        assumptions.append("NetCDF-C dependency inferred from validated companion package")
        confidence = "medium"
        if not linkage.netcdf_c_prefix:
            assumptions.append("NetCDF-C dependency not confirmed via dynamic linkage")
            confidence = "medium"

    mpi_pkg = detected.get("openmpi") or detected.get("mpich") or detected.get("mpi")
    if linkage.mpi_prefix and mpi_pkg and mpi_pkg.found and mpi_pkg.validation and mpi_pkg.validation.valid:
        spec += f" ^{_mpi_dep_spec(mpi_pkg)}"
        assumptions.append("MPI dependency inferred from dynamic linkage")
        confidence = "medium"

    return spec, confidence, assumptions


def _build_spec(
    pkg: DetectedPackage,
    linkage: PackageLinkage,
    detected: Dict[str, DetectedPackage],
) -> PackageSpec:
    prefix = _prefix(pkg)
    if not isinstance(prefix, str) or not prefix:
        raise SpecBuildError(f"package {pkg.name} has no prefix")

    if pkg.name in ("openmpi", "mpi", "mpich"):
        spec, confidence, assumptions = _build_mpi_spec(pkg)
    elif pkg.name == "hdf5":
        spec, confidence, assumptions = _build_hdf5_spec(pkg, detected)
    elif pkg.name == "netcdf-c":
        spec, confidence, assumptions = _build_netcdf_c_spec(pkg, linkage, detected)
    elif pkg.name == "netcdf-fortran":
        spec, confidence, assumptions = _build_netcdf_fortran_spec(pkg, linkage, detected)
    else:
        spec = _base_spec(pkg)
        confidence = "medium"
        assumptions = ["spec generated from package name and detected version only"]

    return PackageSpec(
        package=pkg.name,
        spec=spec,
        prefix=prefix,
        confidence=confidence,
        assumptions=assumptions,
    )


def build_specs(
    detected: Dict[str, DetectedPackage],
    linkage_map: Dict[str, PackageLinkage],
) -> Dict[str, PackageSpec]:
    specs: Dict[str, PackageSpec] = {}

    for name, pkg in detected.items():
        if not pkg.found:
            continue
        if not pkg.validation or not pkg.validation.valid:
            continue

        linkage = linkage_map.get(name, PackageLinkage())
        specs[name] = _build_spec(pkg, linkage, detected)

    return specs
