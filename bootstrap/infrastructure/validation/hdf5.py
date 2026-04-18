from __future__ import annotations

from typing import Dict, Optional

from bootstrap.domain.models import Hdf5ValidationDetails, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_c,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    safe_first_line,
    select_c_compiler,
)


def _resolve_hdf5_tool_and_prefix(tool_paths: Dict[str, str], env: Dict[str, str]) -> tuple[Optional[str], Optional[str]]:
    h5cc = tool_paths.get("h5cc") or tool_paths.get("h5pcc") or tool_paths.get("hp5cc")
    if h5cc:
        return h5cc, infer_prefix_from_tool(h5cc)

    for key in (
        "CRAY_HDF5_PARALLEL_PREFIX",
        "CRAY_HDF5_PREFIX",
        "HDF5_DIR",
        "HDF5_ROOT",
        "HDF5_PREFIX",
    ):
        value = env.get(key)
        if value and value.strip():
            return None, value.strip()

    return None, None


def _build_hdf5_fallback_flags(prefix: str) -> str:
    return f"-I{prefix}/include"


def _build_hdf5_fallback_libs(prefix: str, parallel: bool) -> str:
    if parallel:
        return f"-L{prefix}/lib -lhdf5_hl_parallel -lhdf5_parallel"
    return f"-L{prefix}/lib -lhdf5_hl -lhdf5"


def validate_hdf5(tool_paths: Dict[str, str], env: Dict[str, str], strict: bool) -> ValidationResult:
    h5cc, prefix = _resolve_hdf5_tool_and_prefix(tool_paths, env)
    if not prefix and not h5cc:
        return ValidationResult(valid=False, reason="h5cc/h5pcc or HDF5 prefix hint not found")

    config_head = ""
    show_text = ""
    version: Optional[str] = None
    parallel = False

    if h5cc:
        config_res = run_cmd([h5cc, "-showconfig"], env)
        show_res = run_cmd([h5cc, "-show"], env)
        if not prefix:
            prefix = infer_prefix_from_tool(h5cc)
        config_text = " ".join([config_res.stdout or "", config_res.stderr or ""]).lower()
        parallel = "parallel hdf5: yes" in config_text or "parallel" in (show_res.stdout or "").lower()
        config_head = safe_first_line(config_res.stdout)
        show_text = show_res.stdout.strip()
        version = normalize_version(config_res.stdout)
    else:
        parallel = any(k in env and env.get(k) for k in ("CRAY_HDF5_PARALLEL_PREFIX",))
        config_head = "HDF5 prefix detected from environment"
        show_text = ""
        version = normalize_version(prefix) if prefix else None

    compile_result = None
    if strict:
        compiler = h5cc or select_c_compiler(env)
        if not compiler or not prefix:
            return ValidationResult(
                valid=False,
                reason="no compiler or HDF5 prefix available for validation",
                details=Hdf5ValidationDetails(
                    prefix=prefix,
                    parallel=parallel,
                    show=show_text,
                    config_head=config_head,
                    version=version,
                    compile=None,
                ),
            )

        code = """
        #include "hdf5.h"
        int main(void) {
            hid_t v = H5Pcreate(H5P_FILE_ACCESS);
            H5Pclose(v);
            return 0;
        }
        """
        compile_result = compile_test_c(
            compiler,
            code,
            env,
            flags="" if h5cc else _build_hdf5_fallback_flags(prefix),
            libs="" if h5cc else _build_hdf5_fallback_libs(prefix, parallel),
        )
        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="HDF5 compilation failed",
                details=Hdf5ValidationDetails(
                    prefix=prefix,
                    parallel=parallel,
                    show=show_text,
                    config_head=config_head,
                    version=version,
                    compile=compile_result,
                ),
            )

    return ValidationResult(
        valid=True,
        reason="HDF5 validation passed",
        details=Hdf5ValidationDetails(
            prefix=prefix,
            parallel=parallel,
            show=show_text,
            config_head=config_head,
            version=version,
            compile=compile_result,
        ),
    )
