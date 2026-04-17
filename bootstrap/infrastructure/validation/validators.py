from __future__ import annotations

import logging
from dataclasses import replace
from typing import Dict, Optional

from bootstrap.domain.models import ExecutionContext, PackageDefinition, ValidationResult
from bootstrap.infrastructure.validation.hdf5 import validate_hdf5
from bootstrap.infrastructure.validation.mpi import validate_mpi
from bootstrap.infrastructure.validation.netcdf_c import validate_netcdf_c
from bootstrap.infrastructure.validation.netcdf_fortran import validate_netcdf_fortran
from bootstrap.shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


def _patch_prefix(prefix: Optional[str], result: ValidationResult) -> ValidationResult:
    if not prefix or result.details is None:
        return result

    if hasattr(result.details, "prefix") and getattr(result.details, "prefix"):
        return result

    try:
        patched_details = replace(result.details, prefix=prefix)
    except TypeError:
        return result

    return ValidationResult(
        valid=result.valid,
        reason=result.reason,
        details=patched_details,
        warnings=list(result.warnings),
    )


def validate_package(
    definition: PackageDefinition,
    prefix: Optional[str],
    tool_paths: Dict[str, str],
    env: Dict[str, str],
    context: ExecutionContext,
) -> ValidationResult:
    try:
        if not tool_paths:
            return ValidationResult(valid=False, reason="no tools found")

        validation_type = definition.validation_type
        if validation_type == "mpi":
            result = validate_mpi(definition, tool_paths, env, context)
        elif validation_type == "hdf5":
            result = validate_hdf5(tool_paths, env, context.strict_validation)
        elif validation_type == "netcdf-c":
            result = validate_netcdf_c(tool_paths, env, context.strict_validation)
        elif validation_type == "netcdf-fortran":
            result = validate_netcdf_fortran(tool_paths, env, context.strict_validation)
        else:
            result = ValidationResult(
                valid=False,
                reason=f"unknown validation type: {validation_type}",
            )

        return _patch_prefix(prefix, result)
    except Exception as exc:
        logger.exception("Validation crashed for package %s", definition.name)
        raise ValidationError(f"validation failed for package {definition.name}") from exc
