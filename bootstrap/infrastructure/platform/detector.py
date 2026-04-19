from __future__ import annotations

import platform as py_platform

import archspec.cpu
import distro

from bootstrap.domain.models import PlatformFacts


def _detect_platform_name() -> str:
    system_name = py_platform.system().strip().lower()
    if not system_name:
        return "unknown"
    if system_name == "linux":
        return "linux"
    return system_name


def _normalize_linux_distribution(dist_id: str, version: str) -> tuple[str, str | None]:
    normalized_id = (dist_id or "").strip().lower()
    normalized_version = (version or "").strip()

    if not normalized_id:
        return "linux", None

    major = normalized_version.split(".", 1)[0] if normalized_version else ""
    raw = f"{normalized_id}{normalized_version}" if normalized_version else normalized_id

    if normalized_id in {"rhel", "redhat", "red hat", "redhatenterpriseserver"}:
        return (f"rhel{major}" if major else "rhel"), raw

    if normalized_id == "rocky":
        return (f"rocky{major}" if major else "rocky"), raw

    if normalized_id == "centos":
        return (f"centos{major}" if major else "centos"), raw

    if normalized_id == "ubuntu":
        short = ".".join(normalized_version.split(".")[:2]) if normalized_version else ""
        return (f"ubuntu{short}" if short else "ubuntu"), raw

    return (f"{normalized_id}{major}" if major else normalized_id), raw


def _detect_operating_system() -> tuple[str, str | None]:
    if _detect_platform_name() == "linux":
        return _normalize_linux_distribution(distro.id(), distro.version())
    system_name = py_platform.system().strip().lower()
    return (system_name or "unknown"), (system_name or None)


def _detect_target() -> tuple[str, str | None]:
    host = archspec.cpu.host()
    name = str(getattr(host, "name", "") or "").strip()
    if not name:
        return "unknown", None
    return name, name


def detect_platform_facts() -> PlatformFacts:
    operating_system, raw_operating_system = _detect_operating_system()
    target, raw_target = _detect_target()
    return PlatformFacts(
        platform=_detect_platform_name(),
        operating_system=operating_system,
        target=target,
        source="detection",
        raw_operating_system=raw_operating_system,
        raw_target=raw_target,
    )
