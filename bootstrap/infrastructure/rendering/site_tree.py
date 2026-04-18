from __future__ import annotations

from pathlib import Path
from typing import Optional

from bootstrap.domain.models import DerivedSitePolicy, LayeredSpackStackArtifacts
from bootstrap.infrastructure.rendering.compilers_yaml import generate_compilers_yaml
from bootstrap.infrastructure.rendering.config_yaml import generate_config_yaml
from bootstrap.infrastructure.rendering.modules_yaml import (
    generate_common_modules_yaml_from_policy,
    generate_site_modules_yaml_from_policy,
)
from bootstrap.infrastructure.rendering.packages_yaml import (
    generate_common_packages_yaml_from_policy,
    generate_site_packages_yaml_from_policy,
)
from bootstrap.infrastructure.rendering.template_spack_yaml import generate_template_spack_yaml


def build_spack_stack_artifacts(*, policy: DerivedSitePolicy) -> LayeredSpackStackArtifacts:
    template_spack_yaml = None
    if policy.template.enabled:
        template_spack_yaml = generate_template_spack_yaml(
            policy.template.specs,
            compiler=policy.template.compiler,
        )

    site_compilers_yaml = generate_compilers_yaml([policy.compiler]) if policy.compiler is not None else generate_compilers_yaml([])
    site_config_yaml = generate_config_yaml(policy.runtime) if policy.runtime is not None else generate_config_yaml(
        type("_Runtime", (), {
            "build_jobs": policy.site.build_jobs,
            "install_tree_root": "",
            "build_stage": [],
            "test_stage": "",
            "source_cache": "",
            "misc_cache": "",
        })()
    )

    return LayeredSpackStackArtifacts(
        common_packages_yaml=generate_common_packages_yaml_from_policy(policy),
        common_modules_yaml=generate_common_modules_yaml_from_policy(policy),
        site_packages_yaml=generate_site_packages_yaml_from_policy(policy),
        site_compilers_yaml=site_compilers_yaml,
        site_modules_yaml=generate_site_modules_yaml_from_policy(policy),
        site_config_yaml=site_config_yaml,
        template_spack_yaml=template_spack_yaml,
    )


def write_spack_stack_layout(
    output_root: str,
    *,
    policy: DerivedSitePolicy,
    artifacts: LayeredSpackStackArtifacts,
) -> Optional[str]:
    site = policy.site
    template = policy.template
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
    policy: DerivedSitePolicy,
) -> Optional[str]:
    if not policy.site.enabled or not policy.site.name:
        return None

    artifacts = build_spack_stack_artifacts(policy=policy)
    return write_spack_stack_layout(
        output_root,
        policy=policy,
        artifacts=artifacts,
    )
