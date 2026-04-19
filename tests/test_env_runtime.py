from bootstrap.infrastructure.env.runtime import sanitize_env


def test_sanitize_env_filters_miniforge_and_mambaforge_paths() -> None:
    env = {
        "PATH": ":".join(
            [
                "/usr/bin",
                "/home/user/miniforge3/envs/science/bin",
                "/opt/tools/bin",
                "/home/user/mambaforge/envs/base/bin",
            ]
        )
    }

    sanitized = sanitize_env(env)

    assert sanitized["PATH"] == "/usr/bin:/opt/tools/bin"
