from __future__ import annotations

import yaml


def generate_config_yaml(build_jobs: int) -> str:
    payload = {
        "config": {
            "build_jobs": int(build_jobs),
        }
    }
    return yaml.dump(payload, sort_keys=False)
