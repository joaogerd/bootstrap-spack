from bootstrap.domain.models import (
    CompileCheckDetails,
    NetcdfCValidationDetails,
    ValidationResult,
)
from bootstrap.infrastructure.validation.validators import _patch_prefix


def test_patch_prefix_preserves_nested_compile_details_type() -> None:
    compile_details = CompileCheckDetails(
        ok=True,
        cmd="cc test.c -o test",
        stdout="",
        stderr="",
    )
    result = ValidationResult(
        valid=True,
        reason="ok",
        details=NetcdfCValidationDetails(
            prefix=None,
            version_line="netCDF 4.9.2",
            version="4.9.2",
            cflags="-I/opt/include",
            libs="-L/opt/lib -lnetcdf",
            parallel=True,
            compiler_used="mpicc",
            compile=compile_details,
        ),
    )

    patched = _patch_prefix("/opt/netcdf", result)

    assert patched.details is not None
    assert isinstance(patched.details, NetcdfCValidationDetails)
    assert patched.details.prefix == "/opt/netcdf"
    assert isinstance(patched.details.compile, CompileCheckDetails)
    assert patched.details.compile == compile_details


def test_patch_prefix_keeps_existing_prefix_unchanged() -> None:
    result = ValidationResult(
        valid=True,
        reason="ok",
        details=NetcdfCValidationDetails(
            prefix="/existing",
            version_line="netCDF 4.9.2",
            version="4.9.2",
            cflags="",
            libs="",
            parallel=False,
            compiler_used="cc",
            compile=None,
        ),
    )

    patched = _patch_prefix("/new", result)

    assert patched == result
