from __future__ import annotations

from typing import List

import yaml

from bootstrap.domain.models import DerivedSitePolicy


def _normalized_module_key(module_system: str) -> str:
    module_key = module_system.strip().lower() if module_system else "lmod"
    if module_key not in {"lmod", "tcl"}:
        module_key = "lmod"
    return module_key


def _dump_yaml(payload: dict) -> str:
    return yaml.safe_dump(payload, sort_keys=False)


def generate_common_modules_yaml(module_system: str) -> str:
    module_key = _normalized_module_key(module_system)
    payload = {
        "modules": {
            "default": {
                "enable": [module_key],
            }
        }
    }
    return _dump_yaml(payload)


def generate_common_modules_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    enabled = list(policy.module_policy.common_enabled) if policy.module_policy.common_enabled else list(policy.common_modules_enabled)
    payload = {
        "modules": {
            "default": {
                "enable": enabled,
            }
        }
    }
    return _dump_yaml(payload)


def generate_site_modules_yaml(module_system: str, core_compilers: List[str]) -> str:
    module_key = _normalized_module_key(module_system)
    payload = {
        "modules": {
            "default": {
                "enable": [module_key],
            }
        }
    }

    if module_key == "lmod":
        payload["modules"]["default"]["lmod"] = {
            "core_compilers": list(core_compilers),
            "include": ["openmpi", "python"],
        }

    return _dump_yaml(payload)


def generate_site_modules_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    backend = policy.module_policy.backend or policy.site.module_system
    if not backend:
        return _dump_yaml({"modules": {"default": {}}})

    core_compilers = list(policy.module_policy.site_core_compilers)
    if not core_compilers:
        core_compilers = list(policy.site.core_compilers) if policy.site.core_compilers else ([policy.compiler.spec] if policy.compiler is not None else [])
    return generate_site_modules_yaml(backend, core_compilers)


def generate_modules_yaml(module_system: str, core_compilers: List[str]) -> str:
    payload = yaml.safe_load(generate_common_modules_yaml(module_system))
    site_payload = yaml.safe_load(generate_site_modules_yaml(module_system, core_compilers))
    default = payload.setdefault("modules", {}).setdefault("default", {})
    default.update(site_payload.get("modules", {}).get("default", {}))
    return _dump_yaml(payload)
