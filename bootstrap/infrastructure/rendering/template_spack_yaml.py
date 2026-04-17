from __future__ import annotations

from typing import List, Optional

import yaml


def generate_template_spack_yaml(specs: List[str], compiler: Optional[str] = None) -> str:
    rendered_specs: List[str] = []
    for spec in specs:
        item = spec.strip()
        if not item:
            continue
        if compiler and "%" not in item:
            item = f"{item} %{compiler}"
        rendered_specs.append(item)

    payload = {
        "spack": {
            "specs": rendered_specs,
            "view": False,
        }
    }
    return yaml.dump(payload, sort_keys=False)
