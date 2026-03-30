from __future__ import annotations

from typing import Dict, Optional

import yaml

from bootstrap.domain.models import DetectedPackage, PackageSpec


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

        family = str(pkg.metadata.get("family", "")).lower()
        if family in family_map:
            return family_map[family]

    for name, pkg in detected.items():
        if not pkg.found:
            continue
        if name in family_map:
            return family_map[name]

    return None


def generate_packages_yaml(
    detected: Dict[str, DetectedPackage],
    specs: Dict[str, PackageSpec],
) -> str:
    data: Dict[str, object] = {"packages": {}}

    mpi_provider = _infer_mpi_provider(detected)
    if mpi_provider:
        data["packages"]["all"] = {
            "providers": {
                "mpi": [mpi_provider],
            }
        }

    for name, pkg in detected.items():
        if pkg.found and pkg.validation and pkg.validation.valid and name in specs:
            spec = specs[name]
            package_entry = {
                "externals": [
                    {
                        "spec": spec.spec,
                        "prefix": spec.prefix,
                    }
                ],
                "buildable": False,
            }

            if pkg.validation.reason:
                package_entry["detection"] = pkg.validation.reason

            data["packages"][name] = package_entry
        else:
            data["packages"][name] = {
                "buildable": True,
            }

    return yaml.dump(data, sort_keys=False)
