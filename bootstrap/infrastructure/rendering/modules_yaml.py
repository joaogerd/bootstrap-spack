from __future__ import annotations

from typing import List

import yaml


def _normalized_module_key(module_system: str) -> str:
    module_key = module_system.strip().lower() if module_system else "lmod"
    if module_key not in {"lmod", "tcl"}:
        module_key = "lmod"
    return module_key


def generate_common_modules_yaml(module_system: str) -> str:
    module_key = _normalized_module_key(module_system)
    payload = {
        "modules": {
            "default": {
                "enable": [module_key],
            }
        }
    }
    return yaml.dump(payload, sort_keys=False)


def generate_site_modules_yaml(module_system: str, core_compilers: List[str]) -> str:
    module_key = _normalized_module_key(module_system)
    payload = {"modules": {"default": {}}}
    if module_key == "lmod":
        payload["modules"]["default"]["lmod"] = {
            "core_compilers": list(core_compilers),
        }
    return yaml.dump(payload, sort_keys=False)


def generate_modules_yaml(module_system: str, core_compilers: List[str]) -> str:
    payload = yaml.safe_load(generate_common_modules_yaml(module_system))
    site_payload = yaml.safe_load(generate_site_modules_yaml(module_system, core_compilers))
    default = payload.setdefault("modules", {}).setdefault("default", {})
    default.update(site_payload.get("modules", {}).get("default", {}))
    return yaml.dump(payload, sort_keys=False)
