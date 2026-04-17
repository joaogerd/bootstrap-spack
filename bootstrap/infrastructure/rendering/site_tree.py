from __future__ import annotations

from pathlib import Path
from typing import Optional

from bootstrap.domain.models import CompilerEntry, SiteConfig
from bootstrap.infrastructure.rendering.compilers_yaml import generate_compilers_yaml
from bootstrap.infrastructure.rendering.config_yaml import generate_config_yaml
from bootstrap.infrastructure.rendering.modules_yaml import generate_modules_yaml


def write_site_tree(
    output_root: str,
    *,
    site: SiteConfig,
    packages_yaml: str,
    compiler: CompilerEntry,
) -> Optional[str]:
    if not site.enabled or not site.name:
        return None

    root = Path(output_root)
    if site.layout == "spack-stack":
        site_dir = root / "configs" / "sites" / site.name
    else:
        site_dir = root / "site" / site.name

    site_dir.mkdir(parents=True, exist_ok=True)

    (site_dir / "packages.yaml").write_text(packages_yaml, encoding="utf-8")
    (site_dir / "compilers.yaml").write_text(
        generate_compilers_yaml([compiler]),
        encoding="utf-8",
    )

    core_compilers = list(site.core_compilers) if site.core_compilers else [compiler.spec]
    (site_dir / "modules.yaml").write_text(
        generate_modules_yaml(site.module_system, core_compilers),
        encoding="utf-8",
    )
    (site_dir / "config.yaml").write_text(
        generate_config_yaml(site.build_jobs),
        encoding="utf-8",
    )

    return str(site_dir)
