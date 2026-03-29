from __future__ import annotations

import os
import re
import shlex
import tempfile
from typing import Dict, List, Optional
import logging

from bootstrap.domain.models import ExecutionContext, PackageDefinition, ValidationResult
from bootstrap.shared.command_runner import CommandRunner
from bootstrap.shared.exceptions import ValidationError

logger = logging.getLogger(__name__)
_runner = CommandRunner()


def _run_cmd(args: List[str], env: Dict[str, str]):
    return _runner.run(args, env=env)


def _run_shell(command: str, env: Dict[str, str]):
    return _runner.run_shell(command, env=env)


def _safe_first_line(text: str | None) -> str:
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _infer_prefix_from_tool(tool_path: Optional[str]) -> Optional[str]:
    if not tool_path:
        return None
    return os.path.dirname(os.path.dirname(tool_path))


def _normalize_version(text: str | None) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    if match:
        return match.group(1)
    return None


def _build_compile_command(
    compiler: str,
    source_file: str,
    output_file: str,
    flags: str = "",
    libs: str = "",
) -> List[str]:
    cmd = [compiler, source_file, "-o", output_file]
    if flags.strip():
        cmd.extend(shlex.split(flags))
    if libs.strip():
        cmd.extend(shlex.split(libs))
    return cmd


def _compile_test_c(
    compiler: str,
    code: str,
    env: Dict[str, str],
    flags: str = "",
    libs: str = "",
) -> Dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "test.c")
        exe = os.path.join(tmpdir, "test.exe")

        with open(src, "w", encoding="utf-8") as fh:
            fh.write(code)

        cmd = _build_compile_command(compiler, src, exe, flags=flags, libs=libs)
        result = _run_cmd(cmd, env)

        return {
            "ok": result.returncode == 0,
            "cmd": " ".join(shlex.quote(part) for part in cmd),
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }


def _compile_test_fortran(
    compiler: str,
    code: str,
    env: Dict[str, str],
    flags: str = "",
    libs: str = "",
) -> Dict[str, object]:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "test.f90")
        exe = os.path.join(tmpdir, "test.exe")

        with open(src, "w", encoding="utf-8") as fh:
            fh.write(code)

        cmd = _build_compile_command(compiler, src, exe, flags=flags, libs=libs)
        result = _run_cmd(cmd, env)

        return {
            "ok": result.returncode == 0,
            "cmd": " ".join(shlex.quote(part) for part in cmd),
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }


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


def _validate_mpi(
    definition: PackageDefinition,
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    context: ExecutionContext,
) -> ValidationResult:
    mpi_wrapper = tool_paths.get("mpicc") or tool_paths.get("cc")
    if not mpi_wrapper:
        return ValidationResult(valid=False, reason="MPI compiler wrapper not found")

    version_res = _run_cmd([mpi_wrapper, "--version"], env)
    family_show_res = _run_cmd([mpi_wrapper, "-show"], env)
    family_version_res = _run_shell("mpirun --version || mpiexec --version || true", env)

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
    prefix = _infer_prefix_from_tool(mpi_wrapper)
    version_line = _safe_first_line(version_res.stdout or version_res.stderr)
    warnings: List[str] = []

    metadata: Dict[str, object] = {
        "prefix": prefix,
        "family": family,
        "version_line": version_line,
        "version": _normalize_version(combined),
        "mpi_wrapper": mpi_wrapper,
        "wrapper_show": family_show_res.stdout.strip(),
    }

    if family == "unknown":
        warnings.append("unable to determine MPI family")

    if context.strict_validation:
        code = """
        #include <mpi.h>
        int main(int argc, char **argv) {
            MPI_Init(&argc, &argv);
            MPI_Finalize();
            return 0;
        }
        """
        compile_res = _compile_test_c(mpi_wrapper, code, env)
        metadata["compile"] = compile_res

        if not compile_res["ok"]:
            return ValidationResult(
                valid=False,
                reason="MPI compilation failed",
                metadata=metadata,
                warnings=warnings,
            )

    return ValidationResult(
        valid=True,
        reason="MPI validation passed",
        metadata=metadata,
        warnings=warnings,
    )


def _validate_hdf5(
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    strict: bool,
) -> ValidationResult:
    h5cc = tool_paths.get("h5cc") or tool_paths.get("hp5cc")
    if not h5cc:
        return ValidationResult(valid=False, reason="h5cc/hp5cc not found")

    config_res = _run_cmd([h5cc, "-showconfig"], env)
    show_res = _run_cmd([h5cc, "-show"], env)

    prefix = _infer_prefix_from_tool(h5cc)
    config_text = " ".join([config_res.stdout or "", config_res.stderr or ""]).lower()
    parallel = "parallel hdf5: yes" in config_text

    metadata: Dict[str, object] = {
        "prefix": prefix,
        "parallel": parallel,
        "show": show_res.stdout.strip(),
        "config_head": _safe_first_line(config_res.stdout),
        "version": _normalize_version(config_res.stdout),
    }

    if strict:
        code = """
        #include "hdf5.h"
        int main(void) {
            hid_t v = H5Pcreate(H5P_FILE_ACCESS);
            H5Pclose(v);
            return 0;
        }
        """
        compile_res = _compile_test_c(h5cc, code, env)
        metadata["compile"] = compile_res

        if not compile_res["ok"]:
            return ValidationResult(
                valid=False,
                reason="HDF5 compilation failed",
                metadata=metadata,
            )

    return ValidationResult(
        valid=True,
        reason="HDF5 validation passed",
        metadata=metadata,
    )


def _validate_netcdf_c(
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    strict: bool,
) -> ValidationResult:
    nc_config = tool_paths.get("nc-config")
    if not nc_config:
        return ValidationResult(valid=False, reason="nc-config not found")

    prefix_res = _run_cmd([nc_config, "--prefix"], env)
    version_res = _run_cmd([nc_config, "--version"], env)
    cflags_res = _run_cmd([nc_config, "--cflags"], env)
    libs_res = _run_cmd([nc_config, "--libs"], env)
    has_parallel_res = _run_cmd([nc_config, "--has-parallel"], env)

    has_parallel_text = " ".join([has_parallel_res.stdout or "", has_parallel_res.stderr or ""]).lower()
    parallel = "yes" in has_parallel_text
    prefix = prefix_res.stdout.strip() or _infer_prefix_from_tool(nc_config)

    metadata: Dict[str, object] = {
        "prefix": prefix,
        "version_line": version_res.stdout.strip(),
        "version": _normalize_version(version_res.stdout),
        "cflags": cflags_res.stdout.strip(),
        "libs": libs_res.stdout.strip(),
        "parallel": parallel,
    }

    if strict:
        code = """
        #include <netcdf.h>
        int main(void) {
            int ncid = -1;
            nc_create("test.nc", NC_CLOBBER, &ncid);
            if (ncid >= 0) nc_close(ncid);
            return 0;
        }
        """
        compile_res = _compile_test_c(
            "cc",
            code,
            env,
            flags=cflags_res.stdout.strip(),
            libs=libs_res.stdout.strip(),
        )
        metadata["compile"] = compile_res

        if not compile_res["ok"]:
            return ValidationResult(
                valid=False,
                reason="NetCDF-C compilation failed",
                metadata=metadata,
            )

    return ValidationResult(
        valid=True,
        reason="NetCDF-C validation passed",
        metadata=metadata,
    )


def _select_fortran_compiler(env: Dict[str, str]) -> Optional[str]:
    candidates = ["gfortran", "ifort", "mpif90", "ftn"]
    for compiler in candidates:
        result = _run_shell(f"command -v {shlex.quote(compiler)}", env)
        if result.returncode == 0 and result.stdout.strip():
            return compiler
    return None


def _validate_netcdf_fortran(
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    strict: bool,
) -> ValidationResult:
    nf_config = tool_paths.get("nf-config")
    if not nf_config:
        return ValidationResult(valid=False, reason="nf-config not found")

    prefix_res = _run_cmd([nf_config, "--prefix"], env)
    version_res = _run_cmd([nf_config, "--version"], env)
    fflags_res = _run_cmd([nf_config, "--fflags"], env)
    flibs_res = _run_cmd([nf_config, "--flibs"], env)

    prefix = prefix_res.stdout.strip() or _infer_prefix_from_tool(nf_config)
    compiler = _select_fortran_compiler(env)

    metadata: Dict[str, object] = {
        "prefix": prefix,
        "version_line": version_res.stdout.strip(),
        "version": _normalize_version(version_res.stdout),
        "fflags": fflags_res.stdout.strip(),
        "flibs": flibs_res.stdout.strip(),
        "fc_used": compiler,
    }

    if strict:
        if not compiler:
            return ValidationResult(
                valid=False,
                reason="no Fortran compiler available for NetCDF-Fortran validation",
                metadata=metadata,
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
        compile_res = _compile_test_fortran(
            compiler,
            code,
            env,
            flags=fflags_res.stdout.strip(),
            libs=flibs_res.stdout.strip(),
        )
        metadata["compile"] = compile_res

        if not compile_res["ok"]:
            return ValidationResult(
                valid=False,
                reason="NetCDF-Fortran compilation failed",
                metadata=metadata,
            )

    return ValidationResult(
        valid=True,
        reason="NetCDF-Fortran validation passed",
        metadata=metadata,
    )


def validate_package(
    definition: PackageDefinition,
    prefix: Optional[str],
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    context: ExecutionContext,
) -> ValidationResult:
    try:
        if not tool_paths:
            return ValidationResult(valid=False, reason="no tools found")

        validation_type = definition.validation_type

        if validation_type == "mpi":
            result = _validate_mpi(definition, tool_paths, env, context)
        elif validation_type == "hdf5":
            result = _validate_hdf5(tool_paths, env, context.strict_validation)
        elif validation_type == "netcdf-c":
            result = _validate_netcdf_c(tool_paths, env, context.strict_validation)
        elif validation_type == "netcdf-fortran":
            result = _validate_netcdf_fortran(tool_paths, env, context.strict_validation)
        else:
            result = ValidationResult(
                valid=False,
                reason=f"unknown validation type: {validation_type}",
            )

        if prefix and "prefix" not in result.metadata:
            patched = dict(result.metadata)
            patched["prefix"] = prefix
            return ValidationResult(
                valid=result.valid,
                reason=result.reason,
                metadata=patched,
                warnings=list(result.warnings),
            )

        return result
    except Exception as exc:
        logger.exception("Validation crashed for package %s", definition.name)
        raise ValidationError(f"validation failed for package {definition.name}") from exc
