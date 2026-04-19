from __future__ import annotations

from typing import List, Optional

import yaml

from bootstrap.domain.models import CompilerEntry, DerivedSitePolicy


def generate_compilers_yaml(
    compilers: List[CompilerEntry],
    *,
    operating_system_override: Optional[str] = None,
    target_override: Optional[str] = None,
) -> str:
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
                    "operating_system": operating_system_override or entry.operating_system,
                    "target": target_override or entry.target,
                    "modules": list(entry.modules),
                    "environment": {},
                    "extra_rpaths": [],
                }
            }
        )
    return yaml.dump(data, sort_keys=False)


def generate_compilers_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    if policy.compiler is None:
        return generate_compilers_yaml([])
    return generate_compilers_yaml(
        [policy.compiler],
        operating_system_override=policy.policy_operating_system,
        target_override=policy.policy_target,
    )
