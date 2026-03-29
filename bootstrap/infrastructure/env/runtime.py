from __future__ import annotations

import os
from typing import Dict, Optional


def build_clean_env(base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    source = dict(base_env) if base_env is not None else dict(os.environ)

    whitelist = [
        "PATH",
        "LD_LIBRARY_PATH",
        "LIBRARY_PATH",
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "PKG_CONFIG_PATH",
        "MANPATH",
        "MODULEPATH",
        "LOADEDMODULES",
        "LMOD_SYSTEM_NAME",
        "LMOD_PACKAGE_PATH",
        "LMOD_DIR",
        "LMOD_CMD",
        "MODULESHOME",
        "HOME",
        "USER",
        "SHELL",
        "TERM",
        "LANG",
        "LC_ALL",
        "TMPDIR",
    ]

    clean: Dict[str, str] = {}
    for key in whitelist:
        value = source.get(key)
        if value is not None:
            clean[key] = value

    if "PATH" not in clean:
        clean["PATH"] = os.environ.get("PATH", "")

    return clean


def sanitize_env(env: Dict[str, str]) -> Dict[str, str]:
    sanitized = dict(env)

    blocked_tokens = [
        "anaconda",
        "miniconda",
        "conda",
        "/spack/",
        "/.spack/",
        "/micromamba/",
        "/mamba/",
    ]

    path_entries = sanitized.get("PATH", "").split(":")
    filtered_entries = [
        entry
        for entry in path_entries
        if entry and not any(token in entry.lower() for token in blocked_tokens)
    ]

    sanitized["PATH"] = ":".join(filtered_entries)
    return sanitized


def which_in_env(tool: str, env: Dict[str, str]) -> Optional[str]:
    for path in env.get("PATH", "").split(":"):
        if not path:
            continue

        candidate = os.path.join(path, tool)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None
