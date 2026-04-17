from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Set, Tuple

from bootstrap.domain.models import PackageDefinition, PackageNameResolution


def normalize_package_name(name: str) -> str:
    """Normalize names used by the registry/resolution layer.

    Contract: resolution operates on lowercase names. This function is the single
    place that defines that normalization policy for package names.
    """
    return (name or "").strip().lower()


def _build_alias_index(
    registry: Mapping[str, PackageDefinition],
) -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """Build alias lookup tables for a given registry.

    Returns:
        - alias_to_canonical: maps a normalized alias to a canonical name (also normalized)
        - ambiguous_aliases: maps a normalized alias to a set of canonical names when
          the alias is declared by more than one package definition.
    """
    alias_to_canonical: Dict[str, str] = {}
    ambiguous_aliases: Dict[str, Set[str]] = {}

    for canonical_key, definition in registry.items():
        canonical_norm = normalize_package_name(canonical_key)
        def_name_norm = normalize_package_name(definition.name)

        if canonical_norm != def_name_norm:
            raise ValueError(
                f"inconsistent registry entry: key='{canonical_key}' != definition.name='{definition.name}'"
            )

        for raw_alias in definition.aliases:
            alias_norm = normalize_package_name(raw_alias)
            if not alias_norm:
                continue

            if alias_norm in ambiguous_aliases:
                ambiguous_aliases[alias_norm].add(canonical_norm)
                continue

            existing = alias_to_canonical.get(alias_norm)
            if existing is None:
                alias_to_canonical[alias_norm] = canonical_norm
                continue

            if existing != canonical_norm:
                ambiguous_aliases[alias_norm] = {existing, canonical_norm}
                alias_to_canonical.pop(alias_norm, None)

    return alias_to_canonical, ambiguous_aliases


@dataclass(frozen=True)
class PackageRegistryIndex:
    registry: Mapping[str, PackageDefinition]
    alias_to_canonical: Dict[str, str]
    ambiguous_aliases: Dict[str, Set[str]]

    def resolve(self, requested_name: str) -> PackageNameResolution:
        normalized = normalize_package_name(requested_name)

        if normalized in self.registry:
            return PackageNameResolution(
                requested=requested_name,
                normalized=normalized,
                canonical=normalized,
                status="canonical",
            )

        canonical = self.alias_to_canonical.get(normalized)
        if canonical is not None:
            return PackageNameResolution(
                requested=requested_name,
                normalized=normalized,
                canonical=canonical,
                status="alias",
            )

        if normalized in self.ambiguous_aliases:
            candidates = sorted(self.ambiguous_aliases[normalized])
            return PackageNameResolution(
                requested=requested_name,
                normalized=normalized,
                canonical=None,
                status="ambiguous",
                candidates=candidates,
            )

        return PackageNameResolution(
            requested=requested_name,
            normalized=normalized,
            canonical=None,
            status="unknown",
        )


def build_package_registry_index(registry: Mapping[str, PackageDefinition]) -> PackageRegistryIndex:
    alias_to_canonical, ambiguous_aliases = _build_alias_index(registry)
    return PackageRegistryIndex(
        registry=registry,
        alias_to_canonical=alias_to_canonical,
        ambiguous_aliases=ambiguous_aliases,
    )


def resolve_package_name(
    requested_name: str,
    registry: Mapping[str, PackageDefinition],
) -> PackageNameResolution:
    return build_package_registry_index(registry).resolve(requested_name)


PACKAGES: Dict[str, PackageDefinition] = {
    "openmpi": PackageDefinition(
        name="openmpi",
        aliases=["openmpi", "mpi"],
        tools=["mpicc"],
        validation_type="mpi",
        family="mpi",
    ),
    "mpich": PackageDefinition(
        name="mpich",
        aliases=["mpich", "cray-mpich", "mpi"],
        tools=["mpicc", "cc"],
        validation_type="mpi",
        family="mpi",
    ),
    "netcdf-c": PackageDefinition(
        name="netcdf-c",
        aliases=[
            "netcdf-c",
            "netcdf",
            "cray-netcdf",
            "cray-netcdf-hdf5parallel",
            "cray-parallel-netcdf",
        ],
        tools=["nc-config"],
        validation_type="netcdf-c",
        family="io",
        depends_on_mpi_optional=True,
        depends_on_hdf5=True,
    ),
    "netcdf-fortran": PackageDefinition(
        name="netcdf-fortran",
        aliases=[
            "netcdf-fortran",
            "cray-netcdf",
            "cray-netcdf-hdf5parallel",
            "cray-parallel-netcdf",
        ],
        tools=["nf-config", "nc-config"],
        validation_type="netcdf-fortran",
        family="io",
        depends_on_netcdf_c=True,
    ),
    "hdf5": PackageDefinition(
        name="hdf5",
        aliases=["hdf5", "phdf5", "cray-hdf5", "cray-hdf5-parallel"],
        tools=["h5cc", "h5pcc", "hp5cc"],
        validation_type="hdf5",
        family="io",
        parallel_optional=True,
    ),
}
