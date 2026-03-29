from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import PackageDefinition


PACKAGES: Dict[str, PackageDefinition] = {
    "openmpi": PackageDefinition(
        name="openmpi",
        aliases=["openmpi", "mpi"],
        tools=["mpicc"],
        validation_type="mpi",
        family="mpi",
    ),
    "mpich": PackageDefinition(
        name="mpich",
        aliases=["mpich", "cray-mpich", "mpi"],
        tools=["mpicc", "cc"],
        validation_type="mpi",
        family="mpi",
    ),
    "netcdf-c": PackageDefinition(
        name="netcdf-c",
        aliases=["netcdf-c", "netcdf"],
        tools=["nc-config"],
        validation_type="netcdf-c",
        family="io",
        depends_on_mpi_optional=True,
        depends_on_hdf5=True,
    ),
    "netcdf-fortran": PackageDefinition(
        name="netcdf-fortran",
        aliases=["netcdf-fortran"],
        tools=["nf-config"],
        validation_type="netcdf-fortran",
        family="io",
        depends_on_netcdf_c=True,
    ),
    "hdf5": PackageDefinition(
        name="hdf5",
        aliases=["hdf5", "phdf5"],
        tools=["h5cc", "hp5cc"],
        validation_type="hdf5",
        family="io",
        parallel_optional=True,
    ),
}
