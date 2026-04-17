from bootstrap.domain.models import (
    DetectedPackage,
    Hdf5ValidationDetails,
    MpiValidationDetails,
    NetcdfCValidationDetails,
    NetcdfFortranValidationDetails,
    PackageLinkage,
    ValidationResult,
)
from bootstrap.infrastructure.spec.spec_builder import build_specs


def test_build_specs_prefers_typed_details_for_versions_and_parallel_flags() -> None:
    detected = {
        "openmpi": DetectedPackage(
            name="openmpi",
            found=True,
            prefix="/opt/mpi",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=MpiValidationDetails(
                    prefix="/opt/mpi",
                    family="openmpi",
                    version="4.1.1",
                    version_line="Open MPI 4.1.1",
                    mpi_wrapper="/opt/mpi/bin/mpicc",
                    wrapper_show="gcc ...",
                ),
            ),
        ),
        "hdf5": DetectedPackage(
            name="hdf5",
            found=True,
            prefix="/opt/hdf5",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=Hdf5ValidationDetails(
                    prefix="/opt/hdf5",
                    parallel=True,
                    show="gcc ...",
                    config_head="HDF5 Version: 1.12.2",
                    version="1.12.2",
                ),
            ),
        ),
    }

    specs = build_specs(detected, {"hdf5": PackageLinkage()})

    assert specs["hdf5"].spec == "hdf5@1.12.2 ^openmpi@4.1.1"
    assert specs["hdf5"].confidence == "medium"
    assert any("parallel HDF5" in item for item in specs["hdf5"].assumptions)


def test_build_specs_netcdf_fortran_records_missing_linkage_confirmation() -> None:
    detected = {
        "netcdf-c": DetectedPackage(
            name="netcdf-c",
            found=True,
            prefix="/opt/netcdf-c",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=NetcdfCValidationDetails(
                    prefix="/opt/netcdf-c",
                    version_line="netCDF 4.9.2",
                    version="4.9.2",
                    cflags="",
                    libs="",
                    parallel=False,
                    compiler_used="cc",
                ),
            ),
        ),
        "netcdf-fortran": DetectedPackage(
            name="netcdf-fortran",
            found=True,
            prefix="/opt/netcdf-fortran",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=NetcdfFortranValidationDetails(
                    prefix="/opt/netcdf-fortran",
                    version_line="netCDF-Fortran 4.6.1",
                    version="4.6.1",
                    fflags="",
                    flibs="",
                    fc_used="gfortran",
                ),
            ),
        ),
    }

    specs = build_specs(
        detected,
        {"netcdf-fortran": PackageLinkage(netcdf_c_prefix=None, mpi_prefix=None)},
    )

    assert specs["netcdf-fortran"].spec == "netcdf-fortran@4.6.1 ^netcdf-c@4.9.2"
    assert any("not confirmed via dynamic linkage" in item for item in specs["netcdf-fortran"].assumptions)
