from __future__ import annotations

import os
import platform as py_platform
import re
from typing import Dict, Iterable, Optional

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
    pe_env = (env.get("PE_ENV") or "").strip().lower()
    if pe_env == "gnu":
        return "gcc"
    if pe_env in {"cray", "cce"}:
        return "cce"
    if pe_env == "intel":
        return "oneapi"
    if pe_env in {"nvidia", "nvhpc"}:
        return "nvhpc"
    if pe_env == "aocc":
        return "aocc"
    if pe_env == "amd":
        return "amd"

    basename = os.path.basename(cc_path).lower()
    result = _runner.run([cc_path, "--version"], env=env)
    text = " ".join([result.stdout, result.stderr]).lower()

    if "clang" in basename or "clang" in text:
        return "clang"
    if basename in {"icx", "icc", "ifx", "ifort"} or "oneapi" in text or "intel" in text:
        return "oneapi"
    if basename.startswith("nvc") or basename.startswith("pg"):
        return "nvhpc"
    if basename.startswith("gcc") or "gcc" in text or "gnu" in text:
        return "gcc"
    return basename


def _extract_version(binary: str, env: Dict[str, str]) -> str:
    pe_env = (env.get("PE_ENV") or "").strip().lower()
    if pe_env == "gnu":
        for key in ("GNU_VERSION", "GCC_VERSION", "PE_GCC_LEVEL"):
            value = (env.get(key) or "").strip()
            if re.match(r"^\d+(?:\.\d+)*$", value):
                return value
    if pe_env in {"cray", "cce"}:
        for key in ("CCE_VERSION",):
            value = (env.get(key) or "").strip()
            if re.match(r"^\d+(?:\.\d+)*$", value):
                return value

    result = _runner.run([binary, "--version"], env=env)
    text = " ".join([result.stdout, result.stderr])
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", text)
    return match.group(1) if match else "unknown"


def _candidate_paths(env: Dict[str, str], names: Iterable[str]) -> list[str]:
    found: list[str] = []
    for name in names:
        path = which_in_env(name, env)
        if path and path not in found:
            found.append(path)
    return found


def _toolchain_root(path: str) -> Optional[str]:
    try:
        return os.path.dirname(os.path.dirname(path))
    except Exception:
        return None


def _pick_preferred(candidates: list[str], preferred_names: set[str]) -> Optional[str]:
    for path in candidates:
        if os.path.basename(path) in preferred_names:
            return path
    return candidates[0] if candidates else None


def _is_cray_env(env: Dict[str, str]) -> bool:
    return bool((env.get("PE_ENV") or "").strip()) or bool(env.get("CRAYPE_DIR") or env.get("CRAY_SITE_LIST_DIR"))


def detect_compiler_entry(env: Dict[str, str], loaded_modules: list[str]) -> CompilerEntry:
    cc_env = env.get("CC")
    cxx_env = env.get("CXX")
    fc_env = env.get("FC")
    f77_env = env.get("F77")
    cray_mode = _is_cray_env(env)

    if cray_mode:
        chosen_cc = cc_env or which_in_env("cc", env)
        chosen_cxx = cxx_env or which_in_env("CC", env) or which_in_env("c++", env)
        chosen_fc = fc_env or which_in_env("ftn", env)
        chosen_f77 = f77_env or chosen_fc
        if not chosen_cc or not chosen_cxx or not chosen_fc or not chosen_f77:
            raise DetectionError("unable to detect a complete Cray compiler wrapper toolchain (cc/CC/ftn)")

        family = _infer_compiler_family(chosen_cc, env)
        version = _extract_version(chosen_cc, env)
        spec = f"{family}@{version}" if version != "unknown" else family

        return CompilerEntry(
            spec=spec,
            cc=chosen_cc,
            cxx=chosen_cxx,
            f77=chosen_f77,
            fc=chosen_fc,
            operating_system=_read_os_id(),
            target=_detect_target(),
            modules=list(loaded_modules),
        )

    cc_candidates = [cc_env] if cc_env else []
    cc_candidates += _candidate_paths(env, ["gcc", "cc", "clang"])
    cxx_candidates = [cxx_env] if cxx_env else []
    cxx_candidates += _candidate_paths(env, ["g++", "c++", "clang++"])
    fc_candidates = [fc_env] if fc_env else []
    fc_candidates += _candidate_paths(env, ["gfortran", "f95", "f90", "ifort", "ifx"])
    f77_candidates = [f77_env] if f77_env else []
    f77_candidates += _candidate_paths(env, ["gfortran", "f77", "ifort", "ifx"])

    cc_candidates = [c for c in cc_candidates if c]
    cxx_candidates = [c for c in cxx_candidates if c]
    fc_candidates = [c for c in fc_candidates if c]
    f77_candidates = [c for c in f77_candidates if c]

    if not cc_candidates or not cxx_candidates or not fc_candidates:
        raise DetectionError("unable to detect a complete compiler toolchain (cc/cxx/fc)")

    chosen_cxx = _pick_preferred(cxx_candidates, {"g++", "clang++", "icpx"})
    chosen_fc = _pick_preferred(fc_candidates, {"gfortran", "ifort", "ifx"})
    dominant_root = None
    for path in [chosen_fc, chosen_cxx]:
        if path:
            root = _toolchain_root(path)
            if root and root != "/usr":
                dominant_root = root
                break

    chosen_cc = None
    if cc_env:
        chosen_cc = cc_env
    elif dominant_root:
        preferred = [
            os.path.join(dominant_root, "bin", "gcc"),
            os.path.join(dominant_root, "bin", "clang"),
            os.path.join(dominant_root, "bin", "cc"),
        ]
        for path in preferred:
            if os.path.exists(path):
                chosen_cc = path
                break
    if not chosen_cc:
        chosen_cc = _pick_preferred(cc_candidates, {"gcc", "clang", "cc"})

    chosen_f77 = f77_env or chosen_fc or _pick_preferred(f77_candidates, {"gfortran", "ifort", "ifx", "f77"})

    if not chosen_cc or not chosen_cxx or not chosen_fc or not chosen_f77:
        raise DetectionError("unable to detect a complete compiler toolchain (cc/cxx/fc/f77)")

    family = _infer_compiler_family(chosen_cc, env)
    version = _extract_version(chosen_cc, env)
    spec = f"{family}@{version}" if version != "unknown" else family

    return CompilerEntry(
        spec=spec,
        cc=chosen_cc,
        cxx=chosen_cxx,
        f77=chosen_f77,
        fc=chosen_fc,
        operating_system=_read_os_id(),
        target=_detect_target(),
        modules=list(loaded_modules),
    )
