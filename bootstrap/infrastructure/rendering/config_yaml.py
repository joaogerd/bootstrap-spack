from __future__ import annotations

import yaml

from bootstrap.domain.models import DerivedSitePolicy, SiteRuntimeConfig


def generate_config_yaml(config: SiteRuntimeConfig) -> str:
    payload = {
        "config": {
            "build_jobs": int(config.build_jobs),
            "install_tree": {
                "root": config.install_tree_root,
            },
            "build_stage": list(config.build_stage),
            "test_stage": config.test_stage,
            "source_cache": config.source_cache,
            "misc_cache": config.misc_cache,
        }
    }
    return yaml.dump(payload, sort_keys=False)


def generate_config_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    runtime_policy = policy.runtime_policy
    if runtime_policy is not None and runtime_policy.config is not None:
        return generate_config_yaml(runtime_policy.config)
    if policy.runtime is not None:
        return generate_config_yaml(policy.runtime)
    payload = {
        "config": {
            "build_jobs": int(policy.site.build_jobs),
        }
    }
    return yaml.dump(payload, sort_keys=False)
