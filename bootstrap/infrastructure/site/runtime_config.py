from __future__ import annotations

import getpass
import os
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Optional

from bootstrap.domain.models import SiteConfig, SiteRuntimeConfig


def _first_existing_writable(paths: Iterable[str]) -> Optional[str]:
    for raw in paths:
        if not raw:
            continue
        path = Path(raw).expanduser()
        if path.exists() and os.access(path, os.W_OK | os.X_OK):
            return str(path)
    return None


def _detect_build_jobs(site: SiteConfig, env: Dict[str, str], platform: Optional[str]) -> int:
    env_candidates = [
        env.get("SLURM_CPUS_PER_TASK"),
        env.get("SLURM_CPUS_ON_NODE"),
        env.get("PBS_NP"),
        env.get("OMP_NUM_THREADS"),
    ]
    detected: Optional[int] = None
    for value in env_candidates:
        if value and str(value).isdigit():
            detected = int(value)
            break

    if detected is None:
        cpu_count = os.cpu_count() or 1
        if platform in {"cluster", "cray"}:
            detected = min(cpu_count, 8)
        else:
            detected = min(cpu_count, 16)

    return max(1, min(site.build_jobs, detected))


def _persistent_root(site_name: str, env: Dict[str, str]) -> Path:
    home = Path(env.get("HOME") or str(Path.home())).expanduser()
    return home / ".spack-stack" / site_name


def _scratch_root(site_name: str, env: Dict[str, str]) -> Path:
    user = env.get("USER") or getpass.getuser()
    preferred = _first_existing_writable(
        [
            env.get("LOCAL_SCRATCH", ""),
            env.get("SCRATCH", ""),
            env.get("TMPDIR", ""),
            tempfile.gettempdir(),
            "/var/tmp",
            "/tmp",
        ]
    )
    base = Path(preferred or tempfile.gettempdir())
    return base / user / "spack-stack" / site_name


def detect_site_runtime_config(site: SiteConfig, env: Dict[str, str], platform: Optional[str]) -> SiteRuntimeConfig:
    site_name = site.name or "site"
    persistent_root = _persistent_root(site_name, env)
    scratch_root = _scratch_root(site_name, env)

    install_tree_root = persistent_root / "opt" / "spack"
    source_cache = persistent_root / "cache" / "source"
    misc_cache = persistent_root / "cache" / "misc"
    build_stage = [str(scratch_root / "stage")]
    test_stage = str(scratch_root / "test")

    return SiteRuntimeConfig(
        build_jobs=_detect_build_jobs(site, env, platform),
        install_tree_root=str(install_tree_root),
        build_stage=build_stage,
        test_stage=test_stage,
        source_cache=str(source_cache),
        misc_cache=str(misc_cache),
    )
