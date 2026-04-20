from __future__ import annotations

from typing import Dict, Optional

import yaml

from bootstrap.domain.models import DerivedSitePolicy, DetectedPackage, PackageSpec


def _infer_mpi_provider(detected: Dict[str, DetectedPackage]) -> Optional[str]:
    family_map = {
        "openmpi": "openmpi",
        "mpich": "mpich",
        "intelmpi": "intel-oneapi-mpi",
        "intel": "intel-oneapi-mpi",
    }

    for pkg in detected.values():
        if not pkg.found:
            continue
        if not pkg.validation or not pkg.validation.valid:
            continue

        details = pkg.validation.details
        family = getattr(details, "family", "") if details is not None else ""
        family = str(family).lower()
        if family in family_map:
            return family_map[family]

    for name, pkg in detected.items():
        if not pkg.found:
            continue
        if name in family_map:
            return family_map[name]

    return None


def _promoted_external_names_from_policy(policy: DerivedSitePolicy) -> set[str]:
    if policy.site.external_promotion_mode == "all":
        return set(policy.requested_packages)
    return {provider for items in policy.providers.values() for provider in items}


def generate_common_packages_yaml(detected: Dict[str, DetectedPackage]) -> str:
    data: Dict[str, object] = {"packages": {}}
    mpi_provider = _infer_mpi_provider(detected)
    if mpi_provider:
        data["packages"]["all"] = {
            "providers": {
                "mpi": [mpi_provider],
            }
        }
    return yaml.dump(data, sort_keys=False)


def generate_common_packages_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    data: Dict[str, object] = {"packages": {}}
    providers = dict(policy.provider_policy.providers) if policy.provider_policy.providers else dict(policy.providers)
    if providers:
        data["packages"]["all"] = {
            "providers": providers,
        }
    return yaml.dump(data, sort_keys=False)


def generate_site_packages_yaml(
    detected: Dict[str, DetectedPackage],
    specs: Dict[str, PackageSpec],
) -> str:
    data: Dict[str, object] = {"packages": {}}

    for name, pkg in detected.items():
        if pkg.found and pkg.validation and pkg.validation.valid and name in specs:
            spec = specs[name]
            data["packages"][name] = {
                "externals": [
                    {
                        "spec": spec.spec,
                        "prefix": spec.prefix,
                    }
                ],
                "buildable": False,
            }
        else:
            data["packages"][name] = {
                "buildable": True,
            }

    return yaml.dump(data, sort_keys=False)


def generate_site_packages_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    data: Dict[str, object] = {"packages": {}}
    promoted_names = _promoted_external_names_from_policy(policy)

    if policy.external_packages:
        for name in policy.requested_packages:
            package_policy = policy.external_packages.get(name)
            if package_policy is None:
                data["packages"][name] = {"buildable": True}
                continue

            if package_policy.spec is not None and name in promoted_names:
                data["packages"][name] = {
                    "externals": [
                        {
                            "spec": package_policy.spec.spec,
                            "prefix": package_policy.spec.prefix,
                        }
                    ],
                    "buildable": package_policy.buildable,
                }
            else:
                data["packages"][name] = {
                    "buildable": True,
                }
        return yaml.dump(data, sort_keys=False)

    for name in policy.requested_packages:
        spec = policy.packages.get(name)
        if spec is not None and name in promoted_names:
            data["packages"][name] = {
                "externals": [
                    {
                        "spec": spec.spec,
                        "prefix": spec.prefix,
                    }
                ],
                "buildable": False,
            }
        else:
            data["packages"][name] = {
                "buildable": True,
            }

    return yaml.dump(data, sort_keys=False)


def generate_packages_yaml(
    detected: Dict[str, DetectedPackage],
    specs: Dict[str, PackageSpec],
) -> str:
    common = yaml.safe_load(generate_common_packages_yaml(detected))
    site = yaml.safe_load(generate_site_packages_yaml(detected, specs))

    payload: Dict[str, object] = {"packages": {}}
    payload["packages"].update(common.get("packages", {}))
    payload["packages"].update(site.get("packages", {}))
    return yaml.dump(payload, sort_keys=False)


def generate_packages_yaml_from_policy(policy: DerivedSitePolicy) -> str:
    common = yaml.safe_load(generate_common_packages_yaml_from_policy(policy))
    site = yaml.safe_load(generate_site_packages_yaml_from_policy(policy))

    payload: Dict[str, object] = {"packages": {}}
    payload["packages"].update(common.get("packages", {}))
    payload["packages"].update(site.get("packages", {}))
    return yaml.dump(payload, sort_keys=False)
