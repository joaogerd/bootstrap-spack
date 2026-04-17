from __future__ import annotations

import yaml

from bootstrap.domain.models import SiteRuntimeConfig


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
