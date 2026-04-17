from pathlib import Path

from bootstrap.infrastructure.env.config_loader import load_config


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
