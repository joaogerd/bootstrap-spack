from __future__ import annotations

from bootstrap.application import derive_policy
from bootstrap.domain.models import (
    BootstrapConfig,
    CompilerEntry,
    DetectedHostFacts,
    PlatformFacts,
    SiteConfig,
    SitePolicyOverrides,
    SitePolicyPlatformOverrides,
    SitePolicyRuntimeOverrides,
    TemplateConfig,
)


def _make_config(*, target_override: str | None = None) -> BootstrapConfig:
    return BootstrapConfig(
        platform="linux",
        output_dir="out",
        strict_validation=False,
        modules_to_load=[],
        modules_optional=[],
        external_packages=["openmpi", "hdf5", "netcdf-c", "netcdf-fortran"],
        site=SiteConfig(
            name="egeon",
            layout="spack-stack",
            module_system="lmod",
            build_jobs=8,
            core_compilers=["gcc@9.4.0"],
            policy_overrides=SitePolicyOverrides(
                mpi_provider=[],
                runtime=SitePolicyRuntimeOverrides(),
                platform=SitePolicyPlatformOverrides(target=target_override),
            ),
        ),
        template=TemplateConfig(),
    )


def _make_facts() -> DetectedHostFacts:
    return DetectedHostFacts(
        platform_family="linux",
        module_system="lmod",
        loaded_modules=[],
        optional_modules=[],
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
        packages={},
        linkage={},
        runtime=None,
        platform_facts=PlatformFacts(
            platform="linux",
            operating_system="rhel8",
            target="zen2",
            source="detection",
            raw_operating_system="rhel8.4",
            raw_target="zen2",
        ),
    )


def test_policy_platform_defaults_to_detected_platform_facts() -> None:
    policy = derive_policy.derive_site_policy(config=_make_config(), facts=_make_facts(), specs={})

    assert policy.policy_operating_system == "rhel8"
    assert policy.policy_target == "zen2"
    assert policy.authority["platform.operating_system"].source == "detection"
    assert policy.authority["platform.target"].source == "detection"


def test_policy_platform_target_override_supersedes_detection() -> None:
    policy = derive_policy.derive_site_policy(
        config=_make_config(target_override="core2"),
        facts=_make_facts(),
        specs={},
    )

    assert policy.policy_target == "core2"
    assert policy.authority["platform.target"].source == "override"
    assert policy.authority["platform.target"].supersedes_source == "detection"
