from __future__ import annotations

import os
import re
import shlex
import tempfile
from typing import Dict, List, Optional

from bootstrap.domain.models import CompileCheckDetails
from bootstrap.shared.command_runner import CommandRunner

_runner = CommandRunner()


def run_cmd(args: List[str], env: Dict[str, str]):
    return _runner.run(args, env=env)


def run_shell(command: str, env: Dict[str, str]):
    return _runner.run_shell(command, env=env)


def safe_first_line(text: str | None) -> str:
    if not text:
        return ""
    return text.splitlines()[0].strip()


def infer_prefix_from_tool(tool_path: Optional[str]) -> Optional[str]:
    if not tool_path:
        return None
    return os.path.dirname(os.path.dirname(tool_path))


def normalize_version(text: str | None) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    if match:
        return match.group(1)
    return None


def build_compile_command(
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


def compile_test_c(
    compiler: str,
    code: str,
    env: Dict[str, str],
    flags: str = "",
    libs: str = "",
) -> CompileCheckDetails:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "test.c")
        exe = os.path.join(tmpdir, "test.exe")

        with open(src, "w", encoding="utf-8") as fh:
            fh.write(code)

        cmd = build_compile_command(compiler, src, exe, flags=flags, libs=libs)
        result = run_cmd(cmd, env)
        return CompileCheckDetails(
            ok=result.returncode == 0,
            cmd=result.command,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )


def compile_test_fortran(
    compiler: str,
    code: str,
    env: Dict[str, str],
    flags: str = "",
    libs: str = "",
) -> CompileCheckDetails:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "test.f90")
        exe = os.path.join(tmpdir, "test.exe")

        with open(src, "w", encoding="utf-8") as fh:
            fh.write(code)

        cmd = build_compile_command(compiler, src, exe, flags=flags, libs=libs)
        result = run_cmd(cmd, env)
        return CompileCheckDetails(
            ok=result.returncode == 0,
            cmd=result.command,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )


def select_c_compiler(env: Dict[str, str]) -> Optional[str]:
    candidates = ["cc", "mpicc", "gcc", "clang"]
    for compiler in candidates:
        result = run_shell(f"command -v {shlex.quote(compiler)}", env)
        if result.returncode == 0 and result.stdout.strip():
            return compiler
    return None


def select_fortran_compiler(env: Dict[str, str]) -> Optional[str]:
    candidates = ["ftn", "mpif90", "gfortran", "ifort", "ifx"]
    for compiler in candidates:
        result = run_shell(f"command -v {shlex.quote(compiler)}", env)
        if result.returncode == 0 and result.stdout.strip():
            return compiler
    return None
