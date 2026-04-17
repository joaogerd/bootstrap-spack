from __future__ import annotations

from typing import Iterable

from bootstrap.domain.models import BootstrapResult, PackageSpec


def _iter_lines(result: BootstrapResult) -> Iterable[str]:
    yield "\n=== DETECTION ==="
    for name, pkg in result.detected.items():
        status = "OK" if pkg.found else "FAIL"
        reason = pkg.validation.reason if pkg.validation else ""
        yield f"{status:5} {name:20} {pkg.prefix or '-'} {reason}"

    yield "\n=== TOOLCHAIN ==="
    yield result.toolchain.reason

    yield "\n=== SPECS ==="
    for spec in result.specs.values():
        yield _format_spec(spec)

    if not result.dry_run:
        yield "\n=== OUTPUTS ==="
        yield f"report: {result.output_report}"
        yield f"packages_yaml: {result.output_yaml}"


def _format_spec(spec: PackageSpec) -> str:
    suffix = ""
    if spec.assumptions:
        suffix = f" assumptions={spec.assumptions}"
    return f"{spec.package}: {spec.spec} [{spec.prefix}] confidence={spec.confidence}{suffix}"


def render_console(result: BootstrapResult) -> str:
    return "\n".join(_iter_lines(result)) + "\n"
