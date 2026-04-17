from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import NetcdfCValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_c,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    select_c_compiler,
)


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
    compiler = select_c_compiler(env)

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
                    cflags=cflags_res.stdout.strip(),
                    libs=libs_res.stdout.strip(),
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
            flags=cflags_res.stdout.strip(),
            libs=libs_res.stdout.strip(),
        )

        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="NetCDF-C compilation failed",
                details=NetcdfCValidationDetails(
                    prefix=prefix,
                    version_line=version_res.stdout.strip(),
                    version=normalize_version(version_res.stdout),
                    cflags=cflags_res.stdout.strip(),
                    libs=libs_res.stdout.strip(),
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
            cflags=cflags_res.stdout.strip(),
            libs=libs_res.stdout.strip(),
            parallel=parallel,
            compiler_used=compiler,
            compile=compile_result,
        ),
    )
