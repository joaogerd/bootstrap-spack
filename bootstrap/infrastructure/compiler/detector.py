from __future__ import annotations

import os
import platform as py_platform
import re
from typing import Dict, Optional

from bootstrap.domain.models import CompilerEntry
from bootstrap.infrastructure.env.runtime import which_in_env
from bootstrap.shared.command_runner import CommandRunner
from bootstrap.shared.exceptions import DetectionError

_runner = CommandRunner()


def _read_os_id() -> str:
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as fh:
            data = fh.read()
    except OSError:
        return py_platform.system().lower()

    def _extract(key: str) -> Optional[str]:
        match = re.search(rf"^{key}=(.*)$", data, re.MULTILINE)
        if not match:
            return None
        value = match.group(1).strip().strip('"')
        return value or None

    distro = _extract("ID") or py_platform.system().lower()
    version = _extract("VERSION_ID") or ""
    return f"{distro}{version}" if version else distro


def _detect_target() -> str:
    machine = py_platform.machine().strip()
    return machine or "unknown"


def _infer_compiler_family(cc_path: str, env: Dict[str, str]) -> str:
    basename = os.path.basename(cc_path).lower()
    if basename.startswith("gcc") or basename == "cc":
        result = _runner.run([cc_path, "--version"], env=env)
        text = " ".join([result.stdout, result.stderr]).lower()
        if "gcc" in text or "gnu" in text:
            return "gcc"
        if "clang" in text:
            return "clang"
        if "intel" in text or "oneapi" in text or "icx" in text:
            return "oneapi"
    if "clang" in basename:
        return "clang"
    if basename in {"icx", "icc", "ifx", "ifort"}:
        return "oneapi"
    if basename.startswith("nvc") or basename.startswith("pg"):
        return "nvhpc"
    if basename.startswith("gcc"):
        return "gcc"
    return basename


def _extract_version(binary: str, env: Dict[str, str]) -> str:
    result = _runner.run([binary, "--version"], env=env)
    text = " ".join([result.stdout, result.stderr])
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    return match.group(1) if match else "unknown"


def detect_compiler_entry(env: Dict[str, str], loaded_modules: list[str]) -> CompilerEntry:
    cc = env.get("CC") or which_in_env("cc", env) or which_in_env("gcc", env)
    cxx = env.get("CXX") or which_in_env("c++", env) or which_in_env("g++", env)
    fc = env.get("FC") or which_in_env("gfortran", env) or which_in_env("f95", env) or which_in_env("f90", env)
    f77 = env.get("F77") or fc

    if not cc or not cxx or not fc or not f77:
        raise DetectionError("unable to detect a complete compiler toolchain (cc/cxx/fc/f77)")

    family = _infer_compiler_family(cc, env)
    version = _extract_version(cc, env)
    spec = f"{family}@{version}" if version != "unknown" else family

    return CompilerEntry(
        spec=spec,
        cc=cc,
        cxx=cxx,
        f77=f77,
        fc=fc,
        operating_system=_read_os_id(),
        target=_detect_target(),
        modules=list(loaded_modules),
    )
