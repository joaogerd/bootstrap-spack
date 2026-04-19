from __future__ import annotations

from types import SimpleNamespace

from bootstrap.infrastructure.platform import detector


def test_detect_platform_facts_normalizes_linux_and_target(monkeypatch) -> None:
    monkeypatch.setattr(detector.py_platform, "system", lambda: "Linux")
    monkeypatch.setattr(detector.distro, "id", lambda: "rhel")
    monkeypatch.setattr(detector.distro, "version", lambda: "8.4")
    monkeypatch.setattr(detector.archspec.cpu, "host", lambda: SimpleNamespace(name="zen2"))

    facts = detector.detect_platform_facts()

    assert facts.platform == "linux"
    assert facts.operating_system == "rhel8"
    assert facts.target == "zen2"
    assert facts.raw_operating_system == "rhel8.4"
    assert facts.raw_target == "zen2"
