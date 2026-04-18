from __future__ import annotations

import os
from typing import Dict, Optional
import logging

from bootstrap.domain.models import DetectedPackage, ExecutionContext, PackageDefinition, ValidationResult
from bootstrap.infrastructure.env.runtime import build_clean_env, sanitize_env, which_in_env
from bootstrap.infrastructure.modules.module_system import module_avail, module_load
from bootstrap.infrastructure.validation.validators import validate_package
from bootstrap.shared.exceptions import DetectionError, ModuleSystemError, ValidationError

logger = logging.getLogger(__name__)


def _infer_prefix(tool_path: Optional[str]) -> Optional[str]:
    if not tool_path:
        return None

    if "/bin/" in tool_path:
        return tool_path.split("/bin/")[0]

    parts = tool_path.split("/")
    if len(parts) > 2:
        return "/".join(parts[:-2])

    return None


def _prefix_hint_keys(definition: PackageDefinition) -> list[str]:
    if definition.name == "hdf5":
        return [
            "CRAY_HDF5_PARALLEL_PREFIX",
            "CRAY_HDF5_PREFIX",
            "HDF5_DIR",
            "HDF5_ROOT",
            "HDF5_PREFIX",
        ]
    if definition.name in {"netcdf-c", "netcdf-fortran"}:
        return ["CRAY_NETCDF_PREFIX", "NETCDF_DIR", "NETCDF_ROOT", "NETCDF_PREFIX"]
    return []


def _extract_prefix_hint(definition: PackageDefinition, env: Dict[str, str]) -> Optional[str]:
    for key in _prefix_hint_keys(definition):
        raw_prefix = env.get(key)
        if raw_prefix and raw_prefix.strip():
            return raw_prefix.strip()
    return None


def _collect_tool_paths(tools: list[str], env: Dict[str, str], definition: Optional[PackageDefinition] = None) -> Dict[str, str]:
    found: Dict[str, str] = {}

    for tool in tools:
        path = which_in_env(tool, env)
        if path:
            found[tool] = path

    if definition is None:
        return found

    prefix = _extract_prefix_hint(definition, env)
    if prefix:
        bin_dir = os.path.join(prefix, "bin")
        for tool in tools:
            if tool in found:
                continue
            candidate = os.path.join(bin_dir, tool)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                found[tool] = candidate

    return found


def _collect_module_candidates(definition: PackageDefinition, context: ExecutionContext) -> list[str]:
    names = [definition.name] + list(definition.aliases)

    candidates: list[str] = []
    seen = set()

    for name in names:
        for mod in module_avail(name):
            if mod not in seen:
                seen.add(mod)
                candidates.append(mod)

    for mod in context.optional_modules:
        low = mod.lower()
        if any(alias in low or definition.name in low for alias in definition.aliases + [definition.name]):
            if mod not in seen:
                seen.add(mod)
                candidates.append(mod)

    for mod in context.optional_modules:
        if mod not in seen:
            seen.add(mod)
            candidates.append(mod)

    return candidates


def _build_detected_package(
    definition: PackageDefinition,
    *,
    found: bool,
    prefix: Optional[str],
    method: Optional[str],
    tool_paths: Dict[str, str],
    validation: ValidationResult | None,
) -> DetectedPackage:
    metadata = dict(validation.metadata) if validation is not None else {}

    return DetectedPackage(
        name=definition.name,
        found=found,
        prefix=prefix,
        method=method,
        tool_paths=tool_paths,
        validation=validation,
        metadata=metadata,
    )


def detect_package(
    definition: PackageDefinition,
    context: ExecutionContext,
) -> DetectedPackage:
    try:
        base_env = sanitize_env(build_clean_env(context.base_env))
        logger.info("Detecting package %s", definition.name)
        last_failure: ValidationResult | None = None
        last_failure_prefix: Optional[str] = None
        last_failure_method: Optional[str] = None
        last_failure_tool_paths: Dict[str, str] = {}

        base_tool_paths = _collect_tool_paths(definition.tools, base_env, definition)
        base_prefix_hint = _extract_prefix_hint(definition, base_env)

        if base_tool_paths or base_prefix_hint:
            base_prefix = next(
                (_infer_prefix(path) for path in base_tool_paths.values() if path),
                None,
            ) or base_prefix_hint

            validation = validate_package(
                definition=definition,
                prefix=base_prefix,
                tool_paths=base_tool_paths,
                env=base_env,
                context=context,
            )

            if validation.valid:
                validated_prefix = validation.metadata.get("prefix")
                final_prefix = validated_prefix if isinstance(validated_prefix, str) else base_prefix

                return _build_detected_package(
                    definition,
                    found=True,
                    prefix=final_prefix,
                    method="base-env",
                    tool_paths=base_tool_paths,
                    validation=validation,
                )
            last_failure = validation
            last_failure_prefix = base_prefix
            last_failure_method = "base-env"
            last_failure_tool_paths = base_tool_paths

        candidates = _collect_module_candidates(definition, context)

        for module_name in candidates:
            try:
                module_env = module_load(module_name, base_modules=context.loaded_modules)
            except ModuleSystemError:
                logger.debug("Skipping module candidate %s for %s", module_name, definition.name)
                continue

            candidate_env = sanitize_env(build_clean_env(module_env))
            candidate_tool_paths = _collect_tool_paths(definition.tools, candidate_env, definition)
            candidate_prefix_hint = _extract_prefix_hint(definition, candidate_env)

            if not candidate_tool_paths and not candidate_prefix_hint:
                continue

            candidate_prefix = next(
                (_infer_prefix(path) for path in candidate_tool_paths.values() if path),
                None,
            ) or candidate_prefix_hint

            validation = validate_package(
                definition=definition,
                prefix=candidate_prefix,
                tool_paths=candidate_tool_paths,
                env=candidate_env,
                context=context,
            )

            if validation.valid:
                validated_prefix = validation.metadata.get("prefix")
                final_prefix = validated_prefix if isinstance(validated_prefix, str) else candidate_prefix

                return _build_detected_package(
                    definition,
                    found=True,
                    prefix=final_prefix,
                    method=f"module:{module_name}",
                    tool_paths=candidate_tool_paths,
                    validation=validation,
                )

            last_failure = validation
            last_failure_prefix = candidate_prefix
            last_failure_method = f"module:{module_name}"
            last_failure_tool_paths = candidate_tool_paths

        failure_validation = last_failure or ValidationResult(
            valid=False,
            reason="no valid candidate found",
        )

        return _build_detected_package(
            definition,
            found=False,
            prefix=last_failure_prefix,
            method=last_failure_method,
            tool_paths=last_failure_tool_paths,
            validation=failure_validation,
        )
    except ValidationError:
        raise
    except Exception as exc:
        logger.exception("Detection crashed for package %s", definition.name)
        raise DetectionError(f"detection failed for package {definition.name}") from exc
