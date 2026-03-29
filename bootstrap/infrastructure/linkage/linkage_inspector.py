from __future__ import annotations

import os
import re
from typing import Dict, Optional

from bootstrap.domain.models import DetectedPackage, PackageLinkage
from bootstrap.shared.command_runner import CommandRunner

_runner = CommandRunner()


def _run_ldd(path: str, env: Dict[str, str]) -> str:
    result = _runner.run(["ldd", path], env=env)
    if result.returncode != 0:
        return (result.stdout or result.stderr or "").strip()
    return result.stdout.strip()


def _find_library_file(prefix: str, names: list[str]) -> Optional[str]:
    for libdir in ("lib", "lib64"):
        base = os.path.join(prefix, libdir)
        if not os.path.isdir(base):
            continue

        for name in names:
            candidate = os.path.join(base, name)
            if os.path.exists(candidate):
                return candidate

    return None


def _parse_ldd_paths(ldd_output: str) -> Dict[str, str]:
    linked: Dict[str, str] = {}

    for raw_line in ldd_output.splitlines():
        line = raw_line.strip()
        match = re.match(r"(\S+)\s+=>\s+(\S+)\s+\(", line)
        if match:
            linked[match.group(1)] = match.group(2)

    return linked


def _extract_prefix_from_libpath(libpath: str) -> Optional[str]:
    if not libpath:
        return None

    for marker in ("/lib64/", "/lib/"):
        if marker in libpath:
            return libpath.split(marker)[0]

    return None


def _choose_primary_library(pkg: DetectedPackage) -> Optional[str]:
    if not pkg.prefix:
        return None

    if pkg.name == "netcdf-c":
        return _find_library_file(
            pkg.prefix,
            ["libnetcdf.so", "libnetcdf.so.19", "libnetcdf.so.18"],
        )

    if pkg.name == "netcdf-fortran":
        return _find_library_file(
            pkg.prefix,
            ["libnetcdff.so", "libnetcdff.so.7"],
        )

    if pkg.name == "hdf5":
        return _find_library_file(
            pkg.prefix,
            ["libhdf5.so", "libhdf5_serial.so"],
        )

    return None


def inspect_linkage(pkg: DetectedPackage, env: Dict[str, str]) -> PackageLinkage:
    library = _choose_primary_library(pkg)

    if not library:
        return PackageLinkage()

    ldd_output = _run_ldd(library, env)
    linked_paths = _parse_ldd_paths(ldd_output)

    hdf5_prefix: Optional[str] = None
    mpi_prefix: Optional[str] = None
    netcdf_c_prefix: Optional[str] = None

    for soname, path in linked_paths.items():
        low = soname.lower()
        prefix = _extract_prefix_from_libpath(path)

        if not prefix:
            continue

        if "libhdf5" in low and not hdf5_prefix:
            hdf5_prefix = prefix

        if any(token in low for token in ("libmpi", "libopen-rte", "libopen-pal", "libmpich")) and not mpi_prefix:
            mpi_prefix = prefix

        if pkg.name == "netcdf-fortran" and "libnetcdf" in low and "netcdff" not in low and not netcdf_c_prefix:
            netcdf_c_prefix = prefix

    return PackageLinkage(
        linked_paths=linked_paths,
        hdf5_prefix=hdf5_prefix,
        mpi_prefix=mpi_prefix,
        netcdf_c_prefix=netcdf_c_prefix,
    )
