from bootstrap.application.derive_policy import build_policy_trace, derive_site_policy
from bootstrap.domain.models import (
    AUTHORITY_PRECEDENCE,
    BootstrapConfig,
    CompilerEntry,
    DetectedHostFacts,
    PackageSpec,
    SiteConfig,
    SitePolicyOverrides,
    SitePolicyRuntimeOverrides,
    SiteRuntimeConfig,
    TemplateConfig,
)


def test_derive_site_policy_applies_controlled_overrides() -> None:
    config = BootstrapConfig(
        platform="linux",
        output_dir=".",
        strict_validation=False,
        modules_to_load=[],
        modules_optional=[],
        external_packages=["openmpi"],
        site=SiteConfig(
            name="linux-example",
            layout="spack-stack",
            module_system="lmod",
            build_jobs=8,
            core_compilers=["gcc@11.4.0"],
            policy_overrides=SitePolicyOverrides(
                mpi_provider=["mpich"],
                runtime=SitePolicyRuntimeOverrides(
                    build_jobs=16,
                    install_tree_root="/scratch/custom/opt/spack",
                    build_stage=["/scratch/custom/stage"],
                    test_stage="/scratch/custom/test",
                    source_cache="/scratch/custom/cache/source",
                    misc_cache="/scratch/custom/cache/misc",
                ),
            ),
        ),
        template=TemplateConfig(name="mpas-bundle", specs=["mpas-bundle"], compiler="gcc"),
    )

    facts = DetectedHostFacts(
        platform_family="linux",
        module_system="lmod",
        loaded_modules=[],
        optional_modules=[],
        compiler=CompilerEntry(
            spec="gcc@11.4.0",
            cc="/usr/bin/gcc",
            cxx="/usr/bin/g++",
            f77="/usr/bin/gfortran",
            fc="/usr/bin/gfortran",
            operating_system="ubuntu22.04",
            target="x86_64",
            modules=[],
        ),
        packages={},
        linkage={},
        runtime=SiteRuntimeConfig(
            build_jobs=8,
            install_tree_root="/home/user/.spack-stack/linux-example/opt/spack",
            build_stage=["/tmp/linux-example/stage"],
            test_stage="/tmp/linux-example/test",
            source_cache="/home/user/.spack-stack/linux-example/cache/source",
            misc_cache="/home/user/.spack-stack/linux-example/cache/misc",
        ),
    )

    specs = {
        "openmpi": PackageSpec(
            package="openmpi",
            spec="openmpi@4.1.1",
            prefix="/opt/mpi",
        )
    }

    policy = derive_site_policy(config=config, facts=facts, specs=specs)
    trace = build_policy_trace(config=config, facts=facts, policy=policy, strict=False)

    assert policy.providers["mpi"] == ["mpich"]
    assert policy.runtime is not None
    assert policy.runtime.build_jobs == 16
    assert policy.runtime.install_tree_root == "/scratch/custom/opt/spack"
    assert policy.runtime.build_stage == ["/scratch/custom/stage"]

    assert policy.authority["providers.mpi"].source == "override"
    assert policy.authority["providers.mpi"].overridden_by == "site.policy_overrides.providers.mpi"
    assert policy.authority["providers.mpi"].supersedes_source == "policy"
    assert policy.authority["providers.mpi"].precedence_rank == AUTHORITY_PRECEDENCE["override"]

    assert policy.authority["runtime.build_jobs"].source == "override"
    assert policy.authority["runtime.build_jobs"].overridden_by == "site.policy_overrides.runtime.build_jobs"
    assert policy.authority["runtime.build_jobs"].supersedes_source == "policy"
    assert policy.authority["runtime.build_jobs"].precedence_rank == AUTHORITY_PRECEDENCE["override"]

    assert any(entry.source == "override" for entry in trace.entries)
