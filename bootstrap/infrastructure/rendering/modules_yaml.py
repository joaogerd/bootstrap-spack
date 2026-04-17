from __future__ import annotations

from typing import List

import yaml


def generate_modules_yaml(module_system: str, core_compilers: List[str]) -> str:
    module_key = module_system.strip().lower() if module_system else "lmod"
    if module_key not in {"lmod", "tcl"}:
        module_key = "lmod"

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
        }

    return yaml.dump(payload, sort_keys=False)
