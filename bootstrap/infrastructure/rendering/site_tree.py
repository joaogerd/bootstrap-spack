from __future__ import annotations

from pathlib import Path
from typing import Optional

from bootstrap.domain.models import CompilerEntry, SiteConfig, TemplateConfig
from bootstrap.infrastructure.rendering.compilers_yaml import generate_compilers_yaml
from bootstrap.infrastructure.rendering.config_yaml import generate_config_yaml
from bootstrap.infrastructure.rendering.modules_yaml import (
    generate_common_modules_yaml,
    generate_site_modules_yaml,
)
from bootstrap.infrastructure.rendering.packages_yaml import (
    generate_common_packages_yaml,
    generate_site_packages_yaml,
)
from bootstrap.infrastructure.rendering.template_spack_yaml import generate_template_spack_yaml


def write_site_tree(
    output_root: str,
    *,
    site: SiteConfig,
    template: TemplateConfig,
    compiler: CompilerEntry,
    detected,
    specs,
) -> Optional[str]:
    if not site.enabled or not site.name:
        return None

    root = Path(output_root)
    if site.layout == "spack-stack":
        common_dir = root / "configs" / "common"
        site_dir = root / "configs" / "sites" / site.name
        template_dir = root / "configs" / "templates" / (template.name or "default")
    else:
        common_dir = root / "common"
        site_dir = root / "site" / site.name
        template_dir = root / "templates" / (template.name or "default")

    common_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)
    if template.enabled:
        template_dir.mkdir(parents=True, exist_ok=True)

    common_packages = generate_common_packages_yaml(detected)
    site_packages = generate_site_packages_yaml(detected, specs)

    (common_dir / "packages.yaml").write_text(common_packages, encoding="utf-8")
    (common_dir / "modules.yaml").write_text(
        generate_common_modules_yaml(site.module_system),
        encoding="utf-8",
    )

    (site_dir / "packages.yaml").write_text(site_packages, encoding="utf-8")
    (site_dir / "compilers.yaml").write_text(
        generate_compilers_yaml([compiler]),
        encoding="utf-8",
    )

    core_compilers = list(site.core_compilers) if site.core_compilers else [compiler.spec]
    (site_dir / "modules.yaml").write_text(
        generate_site_modules_yaml(site.module_system, core_compilers),
        encoding="utf-8",
    )
    (site_dir / "config.yaml").write_text(
        generate_config_yaml(site.build_jobs),
        encoding="utf-8",
    )

    if template.enabled:
        (template_dir / "spack.yaml").write_text(
            generate_template_spack_yaml(template.specs, compiler=template.compiler),
            encoding="utf-8",
        )

    return str(site_dir)
