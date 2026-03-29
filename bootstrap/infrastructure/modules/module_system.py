from __future__ import annotations

import logging
import os
import shlex
from typing import Dict, List

from bootstrap.infrastructure.env.runtime import build_clean_env, sanitize_env
from bootstrap.shared.command_runner import CommandRunner
from bootstrap.shared.exceptions import ModuleSystemError

logger = logging.getLogger(__name__)

_runner = CommandRunner()


def _module_support_available(env: Dict[str, str] | None = None) -> bool:
    result = _runner.run_shell("type module >/dev/null 2>&1", env=env)
    return result.returncode == 0


def _parse_env_output(output: str) -> Dict[str, str]:
    parsed: Dict[str, str] = {}

    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key] = value

    return parsed


def _build_module_command(
    modules: List[str],
    *,
    dump_env: bool = True,
    list_modules: bool = False,
) -> str:
    pieces: List[str] = ["module purge >/dev/null 2>&1 || true"]

    for mod in modules:
        pieces.append(f"module load {shlex.quote(mod)}")

    if list_modules:
        pieces.append("module list 2>&1")

    if dump_env:
        pieces.append("env")

    return " && ".join(pieces)


def load_base_modules(modules: List[str]) -> Dict[str, str]:
    if not modules:
        logger.info("No base modules requested; using current sanitized environment")
        return sanitize_env(build_clean_env())

    parent_env = build_clean_env(dict(os.environ))

    if not _module_support_available(parent_env):
        raise ModuleSystemError(
            "module command is not available in this shell, but base modules were requested"
        )

    command = _build_module_command(modules, dump_env=True, list_modules=False)
    result = _runner.run_shell(command, env=parent_env)

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"failed to load modules: {modules}"
        raise ModuleSystemError(detail)

    loaded_env = _parse_env_output(result.stdout)
    logger.info("Loaded base modules: %s", modules)
    return sanitize_env(build_clean_env(loaded_env))


def module_load(module_name: str, *, base_modules: List[str] | None = None) -> Dict[str, str]:
    modules = list(base_modules or []) + [module_name]
    parent_env = build_clean_env(dict(os.environ))

    if not _module_support_available(parent_env):
        raise ModuleSystemError(
            f"module command is not available, cannot load module {module_name!r}"
        )

    command = _build_module_command(modules, dump_env=True, list_modules=False)
    result = _runner.run_shell(command, env=parent_env)

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"failed to load module: {module_name}"
        raise ModuleSystemError(detail)

    loaded_env = _parse_env_output(result.stdout)
    logger.debug("Loaded fallback module: %s", module_name)
    return sanitize_env(build_clean_env(loaded_env))


def module_avail(pattern: str = "") -> List[str]:
    parent_env = build_clean_env(dict(os.environ))

    if not _module_support_available(parent_env):
        return []

    command = f"module -t avail {shlex.quote(pattern)} 2>&1"
    result = _runner.run_shell(command, env=parent_env)
    text = "\n".join([result.stdout or "", result.stderr or ""]).strip()

    modules: List[str] = []
    seen = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.endswith(":"):
            continue
        if line.startswith("/"):
            continue
        if "no module" in line.lower():
            continue
        if line.startswith("----------"):
            continue

        if line not in seen:
            seen.add(line)
            modules.append(line)

    return modules
