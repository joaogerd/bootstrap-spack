from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from bootstrap.application.build_specs import run_build_specs
from bootstrap.application.check_toolchain import run_toolchain_check
from bootstrap.application.derive_policy import (
    build_detected_host_facts,
    build_policy_trace,
    derive_site_policy,
)
from bootstrap.application.detect_packages import detect_requested_packages
from bootstrap.application.inspect_linkage import run_linkage_inspection
from bootstrap.core.package_registry import PACKAGES
from bootstrap.domain.models import BootstrapResult, ExecutionContext
from bootstrap.infrastructure.compiler.detector import detect_compiler_entry
from bootstrap.infrastructure.env.config_loader import load_config
from bootstrap.infrastructure.modules.module_system import load_base_modules
from bootstrap.infrastructure.rendering.packages_yaml import generate_packages_yaml
from bootstrap.infrastructure.rendering.report_writer import write_detection_report
from bootstrap.infrastructure.rendering.site_tree import write_site_tree
from bootstrap.infrastructure.site.runtime_config import detect_site_runtime_config

logger = logging.getLogger(__name__)


class BootstrapService:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def run(
        self,
        output_report: str = "detection-report.txt",
        output_yaml: str = "packages.yaml",
        strict_override: Optional[bool] = None,
        dry_run: bool = False,
        debug: bool = False,
    ) -> BootstrapResult:
        config = load_config(self.config_path)
        strict = strict_override if strict_override is not None else config.strict_validation

        logger.info("Loading base modules")
        base_env = load_base_modules(config.modules_to_load)

        context = ExecutionContext(
            base_env=base_env,
            loaded_modules=list(config.modules_to_load),
            optional_modules=list(config.modules_optional),
            strict_validation=strict,
            platform=config.platform,
        )

        detected = detect_requested_packages(
            requested=list(config.external_packages),
            registry=PACKAGES,
            context=context,
        )
        linkage = run_linkage_inspection(detected=detected, context=context)
        toolchain = run_toolchain_check(detected=detected, linkage=linkage)
        specs = run_build_specs(detected=detected, linkage=linkage)
        packages_yaml = generate_packages_yaml(detected, specs)

        compiler = None
        runtime_config = None
        if config.site.enabled:
            compiler = detect_compiler_entry(base_env, list(config.modules_to_load))
            runtime_config = detect_site_runtime_config(config.site, base_env, config.platform)

        facts = build_detected_host_facts(
            config=config,
            context=context,
            compiler=compiler,
            runtime_config=runtime_config,
            detected=detected,
            linkage=linkage,
        )
        policy = derive_site_policy(config=config, facts=facts, specs=specs)
        trace = build_policy_trace(config=config, facts=facts, policy=policy, strict=strict)

        if not dry_run:
            logger.info("Writing packages.yaml to %s", output_yaml)
            with open(output_yaml, "w", encoding="utf-8") as fh:
                fh.write(packages_yaml)

            logger.info("Writing detection report to %s", output_report)
            write_detection_report(
                output_file=output_report,
                platform=config.platform,
                modules=list(config.modules_to_load),
                detected=detected,
                linkage=linkage,
                specs=specs,
                toolchain=toolchain,
            )

            if config.site.enabled and compiler is not None and runtime_config is not None:
                site_root = str(Path(output_yaml).parent)
                site_dir = write_site_tree(
                    site_root,
                    policy=policy,
                )
                if site_dir:
                    logger.info("Wrote site files to %s", site_dir)

        if debug:
            logger.debug("Toolchain: %s", toolchain.reason)
            for name, spec in specs.items():
                logger.debug(
                    "Spec: %s -> %s (%s) confidence=%s assumptions=%s",
                    name,
                    spec.spec,
                    spec.prefix,
                    spec.confidence,
                    spec.assumptions,
                )

        return BootstrapResult(
            config_path=self.config_path,
            platform=config.platform,
            modules=list(config.modules_to_load),
            packages=list(config.external_packages),
            strict=strict,
            dry_run=dry_run,
            detected=detected,
            linkage=linkage,
            specs=specs,
            toolchain=toolchain,
            output_report=None if dry_run else output_report,
            output_yaml=None if dry_run else output_yaml,
            facts=facts,
            policy=policy,
            trace=trace,
        )
