from __future__ import annotations

import yaml

from bootstrap.domain.models import (
    CompilerEntry,
    DerivedSitePolicy,
    ExternalPackagePolicy,
    ModulePolicy,
    PackageSpec,
    ProviderPolicy,
    SiteConfig,
    TemplateConfig,
    TemplatePolicy,
)
from bootstrap.infrastructure.rendering.compilers_yaml import generate_compilers_yaml_from_policy
from bootstrap.infrastructure.rendering.packages_yaml import generate_site_packages_yaml_from_policy


def _make_policy() -> DerivedSitePolicy:
    openmpi_spec = PackageSpec(
        package="openmpi",
        spec="openmpi@4.1.1%gcc arch=linux-rhel8-zen2",
        prefix="/opt/openmpi",
    )

    return DerivedSitePolicy(
        site=SiteConfig(name="egeon", external_promotion_mode="providers-only"),
        template=TemplateConfig(),
        runtime=None,
        compiler=CompilerEntry(
            spec="gcc@9.4.0",
            cc="/usr/bin/gcc",
            cxx="/usr/bin/g++",
            f77="/usr/bin/gfortran",
            fc="/usr/bin/gfortran",
            operating_system="rhel8.4",
            target="x86_64",
            modules=[],
        ),
        requested_packages=["openmpi", "hdf5", "netcdf-c", "netcdf-fortran"],
        packages={"openmpi": openmpi_spec},
        providers={"mpi": ["openmpi"]},
        common_modules_enabled=["lmod"],
        external_packages={
            "openmpi": ExternalPackagePolicy(
                package="openmpi",
                requested=True,
                spec=openmpi_spec,
                buildable=False,
                source="policy",
                status="validated-external",
            ),
            "hdf5": ExternalPackagePolicy(
                package="hdf5",
                requested=True,
                spec=None,
                buildable=True,
                source="policy",
                status="unresolved",
            ),
            "netcdf-c": ExternalPackagePolicy(
                package="netcdf-c",
                requested=True,
                spec=None,
                buildable=True,
                source="policy",
                status="unresolved",
            ),
            "netcdf-fortran": ExternalPackagePolicy(
                package="netcdf-fortran",
                requested=True,
                spec=None,
                buildable=True,
                source="policy",
                status="unresolved",
            ),
        },
        provider_policy=ProviderPolicy(providers={"mpi": ["openmpi"]}),
        module_policy=ModulePolicy(backend="lmod"),
        runtime_policy=None,
        template_policy=TemplatePolicy(enabled=False),
        authority={},
        policy_platform="linux",
        policy_operating_system="rhel8",
        policy_target="zen2",
    )


def test_compilers_yaml_uses_policy_platform_values() -> None:
    data = yaml.safe_load(generate_compilers_yaml_from_policy(_make_policy()))

    compiler = data["compilers"][0]["compiler"]
    assert compiler["operating_system"] == "rhel8"
    assert compiler["target"] == "zen2"


def test_site_packages_yaml_promotes_only_mpi_by_default() -> None:
    data = yaml.safe_load(generate_site_packages_yaml_from_policy(_make_policy()))
    packages = data["packages"]

    assert packages["openmpi"]["buildable"] is False
    assert packages["openmpi"]["externals"][0]["prefix"] == "/opt/openmpi"

    assert packages["hdf5"] == {"buildable": True}
    assert packages["netcdf-c"] == {"buildable": True}
    assert packages["netcdf-fortran"] == {"buildable": True}
