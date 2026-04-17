from bootstrap.domain.models import (
    DetectedPackage,
    Hdf5ValidationDetails,
    MpiValidationDetails,
    NetcdfCValidationDetails,
    PackageLinkage,
    ValidationResult,
)
from bootstrap.domain.toolchain_policy import check_toolchain


def test_toolchain_policy_uses_typed_details_for_parallel_checks() -> None:
    packages = [
        DetectedPackage(
            name="hdf5",
            found=True,
            prefix="/opt/hdf5",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=Hdf5ValidationDetails(
                    prefix="/opt/hdf5",
                    parallel=True,
                    show="",
                    config_head="",
                    version="1.12.2",
                ),
            ),
        ),
        DetectedPackage(
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
                    parallel=True,
                    compiler_used="mpicc",
                ),
            ),
        ),
    ]

    result = check_toolchain(packages, {"netcdf-c": PackageLinkage()})

    assert result.valid is False
    assert "NetCDF-C parallel sem MPI válido" in result.problems
    assert "HDF5 paralelo sem MPI válido" in result.warnings


def test_toolchain_policy_uses_mpi_family_from_typed_details_for_tokens() -> None:
    packages = [
        DetectedPackage(
            name="openmpi",
            found=True,
            prefix="/custom/mpi",
            validation=ValidationResult(
                valid=True,
                reason="ok",
                details=MpiValidationDetails(
                    prefix="/custom/mpi",
                    family="openmpi",
                    version="4.1.1",
                    version_line="Open MPI 4.1.1",
                    mpi_wrapper="/custom/mpi/bin/mpicc",
                    wrapper_show="gcc ...",
                ),
            ),
        )
    ]

    result = check_toolchain(packages, {})

    assert result.valid is True
    assert "openmpi" in result.tokens
