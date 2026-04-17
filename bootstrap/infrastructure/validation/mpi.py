from __future__ import annotations

import re
from typing import Dict, List, Optional

from bootstrap.domain.models import ExecutionContext, MpiValidationDetails, PackageDefinition, ValidationResult
from bootstrap.infrastructure.validation.common import (
    compile_test_c,
    infer_prefix_from_tool,
    normalize_version,
    run_cmd,
    run_shell,
    safe_first_line,
)


def _infer_mpi_family(combined: str, context: ExecutionContext, compiler_path: str | None) -> str:
    low = combined.lower()

    if "open mpi" in low or "openmpi" in low:
        return "openmpi"
    if "cray mpich" in low or "cray-mpich" in low:
        return "mpich"
    if "mpich" in low:
        return "mpich"
    if "intel mpi" in low or "intelmpi" in low:
        return "intelmpi"
    if context.platform == "cray" and compiler_path and compiler_path.endswith("/cc"):
        return "mpich"
    return "unknown"


def _extract_version_from_text(text: str) -> Optional[str]:
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    return match.group(1) if match else None


def _extract_mpi_version(
    *,
    family: str,
    family_version_text: str,
    wrapper_show: str,
    prefix: Optional[str],
    combined: str,
) -> Optional[str]:
    version = _extract_version_from_text(family_version_text)
    if version:
        return version

    if family == "openmpi":
        if prefix:
            match = re.search(r"/(\d+\.\d+(?:\.\d+)?)(?:/|$)", prefix)
            if match:
                return match.group(1)
        if wrapper_show:
            match = re.search(r"openmpi[^\s/]*/(\d+\.\d+(?:\.\d+)?)", wrapper_show)
            if match:
                return match.group(1)

    return normalize_version(combined)


def validate_mpi(
    definition: PackageDefinition,
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    context: ExecutionContext,
) -> ValidationResult:
    mpi_wrapper = tool_paths.get("mpicc") or tool_paths.get("cc")
    if not mpi_wrapper:
        return ValidationResult(valid=False, reason="MPI compiler wrapper not found")

    version_res = run_cmd([mpi_wrapper, "--version"], env)
    family_show_res = run_cmd([mpi_wrapper, "-show"], env)
    family_version_res = run_shell("mpirun --version || mpiexec --version || true", env)

    combined = " ".join(
        [
            version_res.stdout or "",
            version_res.stderr or "",
            family_show_res.stdout or "",
            family_show_res.stderr or "",
            family_version_res.stdout or "",
            family_version_res.stderr or "",
        ]
    )

    family = _infer_mpi_family(combined, context, mpi_wrapper)
    prefix = infer_prefix_from_tool(mpi_wrapper)
    version_line = safe_first_line(family_version_res.stdout or family_version_res.stderr) or safe_first_line(version_res.stdout or version_res.stderr)
    mpi_version = _extract_mpi_version(
        family=family,
        family_version_text=(family_version_res.stdout or family_version_res.stderr or "").strip(),
        wrapper_show=family_show_res.stdout.strip(),
        prefix=prefix,
        combined=combined,
    )
    warnings: List[str] = []

    compile_result = None
    if context.strict_validation:
        code = """
        #include <mpi.h>
        int main(int argc, char **argv) {
            MPI_Init(&argc, &argv);
            MPI_Finalize();
            return 0;
        }
        """
        compile_result = compile_test_c(mpi_wrapper, code, env)
        if not compile_result.ok:
            return ValidationResult(
                valid=False,
                reason="MPI compilation failed",
                details=MpiValidationDetails(
                    prefix=prefix,
                    family=family,
                    version=mpi_version,
                    version_line=version_line,
                    mpi_wrapper=mpi_wrapper,
                    wrapper_show=family_show_res.stdout.strip(),
                    compile=compile_result,
                ),
                warnings=warnings,
            )

    if family == "unknown":
        warnings.append("unable to determine MPI family")

    return ValidationResult(
        valid=True,
        reason="MPI validation passed",
        details=MpiValidationDetails(
            prefix=prefix,
            family=family,
            version=mpi_version,
            version_line=version_line,
            mpi_wrapper=mpi_wrapper,
            wrapper_show=family_show_res.stdout.strip(),
            compile=compile_result,
        ),
        warnings=warnings,
    )
