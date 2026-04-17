from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import NetcdfFortranValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_fortran,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    select_fortran_compiler,
)


def validate_netcdf_fortran(tool_paths: Dict[str, str], env: Dict[str, str], strict: bool) -> ValidationResult:
    nf_config = tool_paths.get("nf-config")
    if not nf_config:
        return ValidationResult(valid=False, reason="nf-config not found")

    prefix_res = run_cmd([nf_config, "--prefix"], env)
    version_res = run_cmd([nf_config, "--version"], env)
    fflags_res = run_cmd([nf_config, "--fflags"], env)
    flibs_res = run_cmd([nf_config, "--flibs"], env)

    prefix = prefix_res.stdout.strip() or infer_prefix_from_tool(nf_config)
    compiler = select_fortran_compiler(env)

    compile_result = None
    if strict:
        if not compiler:
            return ValidationResult(
                valid=False,
                reason="no Fortran compiler available for NetCDF-Fortran validation",
                details=NetcdfFortranValidationDetails(
                    prefix=prefix,
                    version_line=version_res.stdout.strip(),
                    version=normalize_version(version_res.stdout),
                    fflags=fflags_res.stdout.strip(),
                    flibs=flibs_res.stdout.strip(),
                    fc_used=None,
                    compile=None,
                ),
            )

        code = """
        program test_netcdf
          use netcdf
          implicit none
          integer :: ncid, status
          status = nf90_create("test.nc", NF90_CLOBBER, ncid)
          if (status == nf90_noerr) status = nf90_close(ncid)
        end program test_netcdf
        """
        compile_result = compile_test_fortran(
            compiler,
            code,
            env,
            flags=fflags_res.stdout.strip(),
            libs=flibs_res.stdout.strip(),
        )

        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="NetCDF-Fortran compilation failed",
                details=NetcdfFortranValidationDetails(
                    prefix=prefix,
                    version_line=version_res.stdout.strip(),
                    version=normalize_version(version_res.stdout),
                    fflags=fflags_res.stdout.strip(),
                    flibs=flibs_res.stdout.strip(),
                    fc_used=compiler,
                    compile=compile_result,
                ),
            )

    return ValidationResult(
        valid=True,
        reason="NetCDF-Fortran validation passed",
        details=NetcdfFortranValidationDetails(
            prefix=prefix,
            version_line=version_res.stdout.strip(),
            version=normalize_version(version_res.stdout),
            fflags=fflags_res.stdout.strip(),
            flibs=flibs_res.stdout.strip(),
            fc_used=compiler,
            compile=compile_result,
        ),
    )
