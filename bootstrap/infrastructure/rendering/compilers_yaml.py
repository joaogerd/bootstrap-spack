from __future__ import annotations

from typing import List

import yaml

from bootstrap.domain.models import CompilerEntry


def generate_compilers_yaml(compilers: List[CompilerEntry]) -> str:
    data = {"compilers": []}
    for entry in compilers:
        data["compilers"].append(
            {
                "compiler": {
                    "spec": entry.spec,
                    "paths": {
                        "cc": entry.cc,
                        "cxx": entry.cxx,
                        "f77": entry.f77,
                        "fc": entry.fc,
                    },
                    "flags": {},
                    "operating_system": entry.operating_system,
                    "target": entry.target,
                    "modules": list(entry.modules),
                    "environment": {},
                    "extra_rpaths": [],
                }
            }
        )
    return yaml.dump(data, sort_keys=False)
