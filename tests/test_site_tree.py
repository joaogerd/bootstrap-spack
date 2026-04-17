from pathlib import Path

import yaml

from bootstrap.domain.models import CompilerEntry, SiteConfig
from bootstrap.infrastructure.rendering.site_tree import write_site_tree


def test_write_site_tree_creates_spack_stack_layout(tmp_path: Path) -> None:
    compiler = CompilerEntry(
        spec="gcc@9.4.0",
        cc="/usr/bin/gcc",
        cxx="/usr/bin/g++",
        f77="/usr/bin/gfortran",
        fc="/usr/bin/gfortran",
        operating_system="rhel8",
        target="x86_64",
        modules=["gnu9/9.4.0"],
    )
    site = SiteConfig(
        name="linux-example",
        layout="spack-stack",
        module_system="lmod",
        build_jobs=8,
        core_compilers=["gcc@9.4.0"],
    )

    site_dir = write_site_tree(
        str(tmp_path),
        site=site,
        packages_yaml="packages:\n  openmpi:\n    buildable: false\n",
        compiler=compiler,
    )

    assert site_dir is not None
    root = tmp_path / "configs" / "sites" / "linux-example"
    assert Path(site_dir) == root
    assert (root / "packages.yaml").exists()
    assert (root / "compilers.yaml").exists()
    assert (root / "modules.yaml").exists()
    assert (root / "config.yaml").exists()

    compilers_data = yaml.safe_load((root / "compilers.yaml").read_text(encoding="utf-8"))
    assert compilers_data["compilers"][0]["compiler"]["spec"] == "gcc@9.4.0"

    modules_data = yaml.safe_load((root / "modules.yaml").read_text(encoding="utf-8"))
    assert modules_data["modules"]["default"]["enable"] == ["lmod"]

    config_data = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    assert config_data["config"]["build_jobs"] == 8
