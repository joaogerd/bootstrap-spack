from __future__ import annotations

from typing import Dict

from bootstrap.domain.models import Hdf5ValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_c,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    safe_first_line,
)


def validate_hdf5(tool_paths: Dict[str, str], env: Dict[str, str], strict: bool) -> ValidationResult:
    h5cc = tool_paths.get("h5cc") or tool_paths.get("hp5cc")
    if not h5cc:
        return ValidationResult(valid=False, reason="h5cc/hp5cc not found")

    config_res = run_cmd([h5cc, "-showconfig"], env)
    show_res = run_cmd([h5cc, "-show"], env)

    prefix = infer_prefix_from_tool(h5cc)
    config_text = " ".join([config_res.stdout or "", config_res.stderr or ""]).lower()
    parallel = "parallel hdf5: yes" in config_text

    compile_result = None
    if strict:
        code = """
        #include "hdf5.h"
        int main(void) {
            hid_t v = H5Pcreate(H5P_FILE_ACCESS);
            H5Pclose(v);
            return 0;
        }
        """
        compile_result = compile_test_c(h5cc, code, env)
        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="HDF5 compilation failed",
                details=Hdf5ValidationDetails(
                    prefix=prefix,
                    parallel=parallel,
                    show=show_res.stdout.strip(),
                    config_head=safe_first_line(config_res.stdout),
                    version=normalize_version(config_res.stdout),
                    compile=compile_result,
                ),
            )

    return ValidationResult(
        valid=True,
        reason="HDF5 validation passed",
        details=Hdf5ValidationDetails(
            prefix=prefix,
            parallel=parallel,
            show=show_res.stdout.strip(),
            config_head=safe_first_line(config_res.stdout),
            version=normalize_version(config_res.stdout),
            compile=compile_result,
        ),
    )
