from __future__ import annotations

import yaml

from bootstrap.domain.models import DerivedSitePolicy


def generate_template_spack_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    template_specs = list(policy.template_policy.specs) if policy.template_policy.specs else list(policy.template.specs)
    compiler = policy.template_policy.compiler or policy.template.compiler

    specs: list[str] = []
    for spec in template_specs:
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
