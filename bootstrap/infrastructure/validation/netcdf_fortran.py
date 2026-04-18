from __future__ import annotations

from typing import Dict, Optional, Tuple

from bootstrap.domain.models import NetcdfFortranValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_fortran,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    select_fortran_compiler,
)


def _compiler_from_config(config_tool: str, env: Dict[str, str]) -> Optional[str]:
    fc_res = run_cmd([config_tool, "--fc"], env)
    compiler = fc_res.stdout.strip()
    return compiler or None


def _resolve_fortran_config(tool_paths: Dict[str, str], env: Dict[str, str]) -> Tuple[str | None, str, str, str, str, str | None]:
    nf_config = tool_paths.get("nf-config")
    if nf_config:
        prefix_res = run_cmd([nf_config, "--prefix"], env)
        version_res = run_cmd([nf_config, "--version"], env)
        fflags_res = run_cmd([nf_config, "--fflags"], env)
        flibs_res = run_cmd([nf_config, "--flibs"], env)
        return (
            nf_config,
            prefix_res.stdout.strip() or infer_prefix_from_tool(nf_config) or "",
            version_res.stdout.strip(),
            fflags_res.stdout.strip(),
            flibs_res.stdout.strip(),
            _compiler_from_config(nf_config, env),
        )

    nc_config = tool_paths.get("nc-config")
    if not nc_config:
        return None, "", "", "", "", None

    has_fortran_res = run_cmd([nc_config, "--has-fortran"], env)
    has_fortran_text = " ".join([has_fortran_res.stdout or "", has_fortran_res.stderr or ""]).lower()
    if "yes" not in has_fortran_text:
        return None, "", "", "", "", None

    prefix_res = run_cmd([nc_config, "--prefix"], env)
    version_res = run_cmd([nc_config, "--version"], env)
    fflags_res = run_cmd([nc_config, "--fflags"], env)
    flibs_res = run_cmd([nc_config, "--flibs"], env)
    return (
        nc_config,
        prefix_res.stdout.strip() or infer_prefix_from_tool(nc_config) or "",
        version_res.stdout.strip(),
        fflags_res.stdout.strip(),
        flibs_res.stdout.strip(),
        _compiler_from_config(nc_config, env),
    )


def validate_netcdf_fortran(tool_paths: Dict[str, str], env: Dict[str, str], strict: bool) -> ValidationResult:
    config_tool, prefix, version_line, fflags, flibs, declared_compiler = _resolve_fortran_config(tool_paths, env)
    if not config_tool:
        return ValidationResult(valid=False, reason="nf-config or nc-config with Fortran support not found")

    compiler = declared_compiler or select_fortran_compiler(env)

    compile_result = None
    if strict:
        if not compiler:
            return ValidationResult(
                valid=False,
                reason="no Fortran compiler available for NetCDF-Fortran validation",
                details=NetcdfFortranValidationDetails(
                    prefix=prefix or None,
                    version_line=version_line,
                    version=normalize_version(version_line),
                    fflags=fflags,
                    flibs=flibs,
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
            flags=fflags,
            libs=flibs,
        )

        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="NetCDF-Fortran compilation failed",
                details=NetcdfFortranValidationDetails(
                    prefix=prefix or None,
                    version_line=version_line,
                    version=normalize_version(version_line),
                    fflags=fflags,
                    flibs=flibs,
                    fc_used=compiler,
                    compile=compile_result,
                ),
            )

    return ValidationResult(
        valid=True,
        reason="NetCDF-Fortran validation passed",
        details=NetcdfFortranValidationDetails(
            prefix=prefix or None,
            version_line=version_line,
            version=normalize_version(version_line),
            fflags=fflags,
            flibs=flibs,
            fc_used=compiler,
            compile=compile_result,
        ),
    )
