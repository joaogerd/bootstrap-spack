from __future__ import annotations


class BootstrapError(Exception):
    """Base exception for the bootstrap project."""
    pass


class ConfigError(BootstrapError):
    """Raised when configuration is invalid."""
    pass


class ModuleSystemError(BootstrapError):
    """Raised when module loading/listing fails."""
    pass


class DetectionError(BootstrapError):
    """Raised when package detection fails unexpectedly."""
    pass


class ValidationError(BootstrapError):
    """Raised when package validation fails unexpectedly."""
    pass


class SpecBuildError(BootstrapError):
    """Raised when spec generation fails."""
    pass
