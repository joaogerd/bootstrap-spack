from __future__ import annotations

import yaml

from bootstrap.domain.models import DerivedSitePolicy


def generate_template_spack_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    specs: list[str] = []
    compiler = policy.template_policy.compiler

    for spec in policy.template_policy.specs:
        rendered = spec
        if compiler:
            rendered = f"{spec} %{compiler}"
        specs.append(rendered)

    data = {
        "spack": {
            "specs": specs,
        }
    }
    return yaml.dump(data, sort_keys=False)
