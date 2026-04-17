from __future__ import annotations

from typing import Dict, Optional

from bootstrap.domain.models import NetcdfCValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_c,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    run_shell,
    select_c_compiler,
)


def _choose_netcdf_c_compiler(env: Dict[str, str], parallel: bool) -> Optional[str]:
    if parallel:
        res = run_shell("command -v mpicc", env)
        if res.returncode == 0 and res.stdout.strip():
            return "mpicc"
    return select_c_compiler(env)


def _normalize_netcdf_c_flags_and_libs(nc_config: str, env: Dict[str, str], cflags: str, libs: str) -> tuple[str, str]:
    normalized_cflags = cflags.strip()
    normalized_libs = libs.strip()

    if normalized_cflags and normalized_libs:
        return normalized_cflags, normalized_libs

    include_res = run_cmd([nc_config, "--includedir"], env)
    libdir_res = run_cmd([nc_config, "--libdir"], env)

    includedir = include_res.stdout.strip()
    libdir = libdir_res.stdout.strip()

    if not normalized_cflags and includedir:
        normalized_cflags = f"-I{includedir}"
    if not normalized_libs and libdir:
        normalized_libs = f"-L{libdir} -lnetcdf"

    return normalized_cflags, normalized_libs


def validate_netcdf_c(tool_paths: Dict[str, str], env: Dict[str, str], strict: bool) -> ValidationResult:
    nc_config = tool_paths.get("nc-config")
    if not nc_config:
        return ValidationResult(valid=False, reason="nc-config not found")

    prefix_res = run_cmd([nc_config, "--prefix"], env)
    version_res = run_cmd([nc_config, "--version"], env)
    cflags_res = run_cmd([nc_config, "--cflags"], env)
    libs_res = run_cmd([nc_config, "--libs"], env)
    has_parallel_res = run_cmd([nc_config, "--has-parallel"], env)

    has_parallel_text = " ".join([has_parallel_res.stdout or "", has_parallel_res.stderr or ""]).lower()
    parallel = "yes" in has_parallel_text
    prefix = prefix_res.stdout.strip() or infer_prefix_from_tool(nc_config)
    compiler = _choose_netcdf_c_compiler(env, parallel=parallel)
    normalized_cflags, normalized_libs = _normalize_netcdf_c_flags_and_libs(
        nc_config,
        env,
        cflags_res.stdout,
        libs_res.stdout,
    )

    compile_result = None
    if strict:
        if not compiler:
            return ValidationResult(
                valid=False,
                reason="no C compiler available for NetCDF-C validation",
                details=NetcdfCValidationDetails(
                    prefix=prefix,
                    version_line=version_res.stdout.strip(),
                    version=normalize_version(version_res.stdout),
                    cflags=normalized_cflags,
                    libs=normalized_libs,
                    parallel=parallel,
                    compiler_used=None,
                    compile=None,
                ),
            )

        code = """
        #include <netcdf.h>
        int main(void) {
            int ncid = -1;
            nc_create("test.nc", NC_CLOBBER, &ncid);
            if (ncid >= 0) nc_close(ncid);
            return 0;
        }
        """
        compile_result = compile_test_c(
            compiler,
            code,
            env,
            flags=normalized_cflags,
            libs=normalized_libs,
        )

        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="NetCDF-C compilation failed",
                details=NetcdfCValidationDetails(
                    prefix=prefix,
                    version_line=version_res.stdout.strip(),
                    version=normalize_version(version_res.stdout),
                    cflags=normalized_cflags,
                    libs=normalized_libs,
                    parallel=parallel,
                    compiler_used=compiler,
                    compile=compile_result,
                ),
            )

    return ValidationResult(
        valid=True,
        reason="NetCDF-C validation passed",
        details=NetcdfCValidationDetails(
            prefix=prefix,
            version_line=version_res.stdout.strip(),
            version=normalize_version(version_res.stdout),
            cflags=normalized_cflags,
            libs=normalized_libs,
            parallel=parallel,
            compiler_used=compiler,
            compile=compile_result,
        ),
    )
