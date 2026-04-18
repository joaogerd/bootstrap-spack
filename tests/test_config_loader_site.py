from pathlib import Path

import pytest

from bootstrap.infrastructure.env.config_loader import load_config
from bootstrap.shared.exceptions import ConfigError


def test_load_config_parses_site_and_template_sections(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: linux
modules:
  load: []
  optional: []
packages:
  external:
    - openmpi
validation:
  strict: true
site:
  name: linux-example
  layout: spack-stack
  module_system: lmod
  build_jobs: 12
  core_compilers:
    - gcc@9.4.0
template:
  name: mpas-bundle
  specs:
    - mpas-bundle
  compiler: gcc
output:
  directory: .
""".strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = load_config(str(config_file))

    assert cfg.platform == "linux"
    assert cfg.site.name == "linux-example"
    assert cfg.site.layout == "spack-stack"
    assert cfg.site.module_system == "lmod"
    assert cfg.site.build_jobs == 12
    assert cfg.site.core_compilers == ["gcc@9.4.0"]
    assert cfg.site.enabled is True
    assert cfg.template.name == "mpas-bundle"
    assert cfg.template.specs == ["mpas-bundle"]
    assert cfg.template.compiler == "gcc"
    assert cfg.template.enabled is True


def test_load_config_parses_site_policy_overrides(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: linux
modules:
  load: []
packages:
  external:
    - openmpi
site:
  name: linux-example
  layout: spack-stack
  policy_overrides:
    providers:
      mpi:
        - mpich
    runtime:
      build_jobs: 16
      install_tree_root: /scratch/site/spack/opt
      build_stage:
        - /scratch/site/spack/stage
      test_stage: /scratch/site/spack/test
      source_cache: /scratch/site/spack/cache/source
      misc_cache: /scratch/site/spack/cache/misc
output:
  directory: .
""".strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = load_config(str(config_file))

    assert cfg.site.policy_overrides.mpi_provider == ["mpich"]
    assert cfg.site.policy_overrides.runtime.build_jobs == 16
    assert cfg.site.policy_overrides.runtime.install_tree_root == "/scratch/site/spack/opt"
    assert cfg.site.policy_overrides.runtime.build_stage == ["/scratch/site/spack/stage"]
    assert cfg.site.policy_overrides.runtime.test_stage == "/scratch/site/spack/test"
    assert cfg.site.policy_overrides.runtime.source_cache == "/scratch/site/spack/cache/source"
    assert cfg.site.policy_overrides.runtime.misc_cache == "/scratch/site/spack/cache/misc"


def test_load_config_rejects_unsupported_site_layout(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: linux
modules:
  load: []
packages:
  external:
    - openmpi
site:
  name: linux-example
  layout: generic
output:
  directory: .
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="site.layout"):
        load_config(str(config_file))


def test_load_config_requires_template_name_when_specs_are_present(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
platform: linux
modules:
  load: []
packages:
  external:
    - openmpi
template:
  specs:
    - mpas-bundle
output:
  directory: .
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="template.name"):
        load_config(str(config_file))
