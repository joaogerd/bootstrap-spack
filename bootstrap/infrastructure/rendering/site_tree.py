from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from bootstrap.domain.models import (
    CompilerEntry,
    LayeredSpackStackArtifacts,
    SiteConfig,
    TemplateConfig,
)
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


def build_spack_stack_artifacts(
    *,
    site: SiteConfig,
    template: TemplateConfig,
    compiler: CompilerEntry,
    detected,
    specs,
) -> LayeredSpackStackArtifacts:
    core_compilers = list(site.core_compilers) if site.core_compilers else [compiler.spec]
    template_spack_yaml = None
    if template.enabled:
        template_spack_yaml = generate_template_spack_yaml(template.specs, compiler=template.compiler)

    return LayeredSpackStackArtifacts(
        common_packages_yaml=generate_common_packages_yaml(detected),
        common_modules_yaml=generate_common_modules_yaml(site.module_system),
        site_packages_yaml=generate_site_packages_yaml(detected, specs),
        site_compilers_yaml=generate_compilers_yaml([compiler]),
        site_modules_yaml=generate_site_modules_yaml(site.module_system, core_compilers),
        site_config_yaml=generate_config_yaml(site.build_jobs),
        template_spack_yaml=template_spack_yaml,
    )


def write_spack_stack_layout(
    output_root: str,
    *,
    site: SiteConfig,
    template: TemplateConfig,
    artifacts: LayeredSpackStackArtifacts,
) -> Optional[str]:
    if not site.enabled or not site.name:
        return None

    root = Path(output_root)
    common_dir = root / "configs" / "common"
    site_dir = root / "configs" / "sites" / site.name
    template_name = template.name if template.name else None
    template_dir = root / "configs" / "templates" / template_name if template_name else None

    common_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)
    if template.enabled and template_dir is not None:
        template_dir.mkdir(parents=True, exist_ok=True)

    (common_dir / "packages.yaml").write_text(artifacts.common_packages_yaml, encoding="utf-8")
    (common_dir / "modules.yaml").write_text(artifacts.common_modules_yaml, encoding="utf-8")

    (site_dir / "packages.yaml").write_text(artifacts.site_packages_yaml, encoding="utf-8")
    (site_dir / "compilers.yaml").write_text(artifacts.site_compilers_yaml, encoding="utf-8")
    (site_dir / "modules.yaml").write_text(artifacts.site_modules_yaml, encoding="utf-8")
    (site_dir / "config.yaml").write_text(artifacts.site_config_yaml, encoding="utf-8")

    if template.enabled and template_dir is not None and artifacts.template_spack_yaml is not None:
        (template_dir / "spack.yaml").write_text(artifacts.template_spack_yaml, encoding="utf-8")

    return str(site_dir)


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

    artifacts = build_spack_stack_artifacts(
        site=site,
        template=template,
        compiler=compiler,
        detected=detected,
        specs=specs,
    )
    return write_spack_stack_layout(
        output_root,
        site=site,
        template=template,
        artifacts=artifacts,
    )
