from bootstrap.domain.models import SiteConfig
from bootstrap.infrastructure.site.runtime_config import detect_site_runtime_config


def test_detect_site_runtime_config_prefers_scratch_and_home_policy(tmp_path, monkeypatch) -> None:
    scratch = tmp_path / "scratch"
    home = tmp_path / "home"
    scratch.mkdir()
    home.mkdir()

    monkeypatch.setattr("bootstrap.infrastructure.site.runtime_config.os.cpu_count", lambda: 64)

    env = {
        "HOME": str(home),
        "USER": "joao",
        "SCRATCH": str(scratch),
    }
    site = SiteConfig(name="egeon", build_jobs=8)

    runtime = detect_site_runtime_config(site, env, platform="cluster")

    assert runtime.build_jobs == 8
    assert runtime.install_tree_root == str(home / ".spack-stack" / "egeon" / "opt" / "spack")
    assert runtime.source_cache == str(home / ".spack-stack" / "egeon" / "cache" / "source")
    assert runtime.misc_cache == str(home / ".spack-stack" / "egeon" / "cache" / "misc")
    assert runtime.build_stage == [str(scratch / "joao" / "spack-stack" / "egeon" / "stage")]
    assert runtime.test_stage == str(scratch / "joao" / "spack-stack" / "egeon" / "test")
