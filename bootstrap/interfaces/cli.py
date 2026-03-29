from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bootstrap.services.bootstrap_service import BootstrapService
from bootstrap.shared.exceptions import BootstrapError
from bootstrap.shared.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bootstrap",
        description="Detect external HPC packages and generate Spack bootstrap data",
    )

    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--report-name", default="detection-report.txt")
    parser.add_argument("--packages-yaml-name", default="packages.yaml")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--strict",
        choices=["true", "false"],
        help="Override strict validation from config",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(debug=args.debug)

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    if not config_path.is_file():
        print(f"[ERROR] Config path is not a file: {config_path}")
        sys.exit(1)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[ERROR] Failed to create output directory '{output_dir}': {exc}")
        sys.exit(1)

    strict_override = None
    if args.strict == "true":
        strict_override = True
    elif args.strict == "false":
        strict_override = False

    service = BootstrapService(str(config_path))

    try:
        result = service.run(
            output_report=str(output_dir / args.report_name),
            output_yaml=str(output_dir / args.packages_yaml_name),
            strict_override=strict_override,
            dry_run=args.dry_run,
            debug=args.debug,
        )
    except BootstrapError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(2)
    except Exception as exc:
        print(f"[ERROR] Unexpected execution failure: {exc}")
        if args.debug:
            raise
        sys.exit(2)

    print("\n=== DETECTION ===")
    for name, pkg in result["detected"].items():
        status = "OK" if pkg.found else "FAIL"
        reason = pkg.validation.reason if pkg.validation else ""
        print(f"{status:5} {name:20} {pkg.prefix or '-'} {reason}")

    print("\n=== TOOLCHAIN ===")
    print(result["toolchain"].reason)

    print("\n=== SPECS ===")
    for spec in result["specs"].values():
        print(f"{spec.package}: {spec.spec} [{spec.prefix}]")

    if not args.dry_run:
        print("\n=== OUTPUTS ===")
        print(f"report: {result['output_report']}")
        print(f"packages_yaml: {result['output_yaml']}")
