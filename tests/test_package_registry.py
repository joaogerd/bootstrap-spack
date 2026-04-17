import pytest

from bootstrap.core.package_registry import (
    build_package_registry_index,
    normalize_package_name,
    resolve_package_name,
)
from bootstrap.domain.models import PackageDefinition


REGISTRY = {
    "alpha": PackageDefinition(
        name="alpha",
        aliases=["a", "shared"],
        tools=["alpha-tool"],
        validation_type="alpha",
        family="test",
    ),
    "beta": PackageDefinition(
        name="beta",
        aliases=["b", "shared"],
        tools=["beta-tool"],
        validation_type="beta",
        family="test",
    ),
}


def test_package_registry_resolves_canonical_alias_and_ambiguous_names() -> None:
    index = build_package_registry_index(REGISTRY)

    assert normalize_package_name("  ALPHA  ") == "alpha"
    assert index.resolve("alpha").status == "canonical"
    assert index.resolve("a").canonical == "alpha"

    ambiguous = index.resolve("shared")
    assert ambiguous.status == "ambiguous"
    assert ambiguous.candidates == ["alpha", "beta"]

    unknown = resolve_package_name("gamma", REGISTRY)
    assert unknown.status == "unknown"
    assert unknown.canonical is None


def test_package_registry_rejects_inconsistent_canonical_definition() -> None:
    bad_registry = {
        "alpha": PackageDefinition(
            name="different-name",
            aliases=["a"],
            tools=["alpha-tool"],
            validation_type="alpha",
            family="test",
        )
    }

    with pytest.raises(ValueError, match="inconsistent registry entry"):
        build_package_registry_index(bad_registry)
