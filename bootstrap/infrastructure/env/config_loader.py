from __future__ import annotations

from typing import Any, Dict

import yaml

from bootstrap.domain.models import BootstrapConfig, SUPPORTED_SITE_LAYOUTS, SiteConfig, TemplateConfig
from bootstrap.shared.exceptions import ConfigError


def _get(data: Dict[str, Any], path: list[str], default=None):
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _require_list(name: str, value: Any) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise ConfigError(f"{name} must be a list")

    converted: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"{name} must contain only non-empty strings")
        converted.append(item.strip())

    return converted


def _load_site_config(raw: Dict[str, Any]) -> SiteConfig:
    site_name = _get(raw, ["site", "name"])
    if site_name is not None and (not isinstance(site_name, str) or not site_name.strip()):
        raise ConfigError("site.name must be a non-empty string when provided")

    layout = _get(raw, ["site", "layout"], "spack-stack")
    if not isinstance(layout, str) or not layout.strip():
        raise ConfigError("site.layout must be a non-empty string")
    layout = layout.strip()
    if layout not in SUPPORTED_SITE_LAYOUTS:
        raise ConfigError(f"site.layout must be one of {SUPPORTED_SITE_LAYOUTS}")

    module_system = _get(raw, ["site", "module_system"], "lmod")
    if not isinstance(module_system, str) or not module_system.strip():
        raise ConfigError("site.module_system must be a non-empty string")

    build_jobs = _get(raw, ["site", "build_jobs"], 8)
    if not isinstance(build_jobs, int) or build_jobs <= 0:
        raise ConfigError("site.build_jobs must be a positive integer")

    core_compilers = _require_list("site.core_compilers", _get(raw, ["site", "core_compilers"], []))

    return SiteConfig(
        name=site_name.strip() if isinstance(site_name, str) else None,
        layout=layout,
        module_system=module_system.strip(),
        build_jobs=build_jobs,
        core_compilers=core_compilers,
    )


def _load_template_config(raw: Dict[str, Any]) -> TemplateConfig:
    template_name = _get(raw, ["template", "name"])
    if template_name is not None and (not isinstance(template_name, str) or not template_name.strip()):
        raise ConfigError("template.name must be a non-empty string when provided")

    compiler = _get(raw, ["template", "compiler"])
    if compiler is not None and (not isinstance(compiler, str) or not compiler.strip()):
        raise ConfigError("template.compiler must be a non-empty string when provided")

    specs = _require_list("template.specs", _get(raw, ["template", "specs"], []))
    if specs and template_name is None:
        raise ConfigError("template.name is required when template.specs is provided")

    return TemplateConfig(
        name=template_name.strip() if isinstance(template_name, str) else None,
        specs=specs,
        compiler=compiler.strip() if isinstance(compiler, str) else None,
    )


def load_config(path: str) -> BootstrapConfig:
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw = yaml.safe_load(file) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"failed to read configuration file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML configuration: {path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("configuration root must be a mapping")

    platform = raw.get("platform")
    if platform is not None and (not isinstance(platform, str) or not platform.strip()):
        raise ConfigError("platform must be a non-empty string when provided")

    output_dir = _get(raw, ["output", "directory"], ".")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ConfigError("output.directory must be a non-empty string")

    strict_validation = _get(raw, ["validation", "strict"], False)
    if not isinstance(strict_validation, bool):
        raise ConfigError("validation.strict must be boolean")

    modules_to_load = _require_list("modules.load", _get(raw, ["modules", "load"], []))
    modules_optional = _require_list("modules.optional", _get(raw, ["modules", "optional"], []))
    external_packages = _require_list("packages.external", _get(raw, ["packages", "external"], []))

    if not external_packages:
        raise ConfigError("packages.external cannot be empty")

    return BootstrapConfig(
        platform=platform.strip() if isinstance(platform, str) else None,
        output_dir=output_dir.strip(),
        strict_validation=strict_validation,
        modules_to_load=modules_to_load,
        modules_optional=modules_optional,
        external_packages=external_packages,
        site=_load_site_config(raw),
        template=_load_template_config(raw),
    )
