"""Main CLI entry point for MTGA Registrar.

This module provides command-line argument parsing, configuration loading,
and execution invocation for the [`ApplicationController`](src/core/app.py).
"""

import argparse
import logging
import sys
from typing import Optional

from src.core.app import ApplicationController
from src.core.config import Settings, setup_logging
from src.core.exceptions import MTGARegistrarError
from src.export.base import ClipboardTransferProvider, ExportTransferProvider
from src.export.server import LocalHTTPServerProvider
from src.export.tunnelmole import TunnelmoleTransferProvider

logger = logging.getLogger("mtga_registrar.main")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the application.

    Returns:
        Parsed command-line arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="MTGA Registrar — Automated MTGA Collection Exporter for GeForce Now"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run export workflow in dry-run mode without executing "
            "physical input or transfer actions."
        ),
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO).",
    )
    parser.add_argument(
        "--max-batch-size",
        type=int,
        default=250,
        help="Maximum number of cards per exported deck batch (default: 250).",
    )
    parser.add_argument(
        "--transfer-mode",
        type=str,
        default="clipboard",
        choices=["clipboard", "server", "tunnelmole"],
        help="Export transfer provider mode (default: clipboard).",
    )
    parser.add_argument(
        "--server-host",
        type=str,
        default="127.0.0.1",
        help="Local HTTP server host (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=8000,
        help="Local HTTP server port (default: 8000).",
    )
    return parser.parse_args()


def main() -> int:
    """Execute the MTGA Registrar application CLI workflow.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_arguments()

    settings = Settings(
        log_level=args.log_level,
        max_batch_size=args.max_batch_size,
    )
    setup_logging(settings.log_level)

    logger.info("Starting MTGA Registrar CLI...")
    logger.info(
        "Configuration: dry_run=%s, log_level=%s, max_batch_size=%d, transfer_mode=%s",
        args.dry_run,
        args.log_level,
        args.max_batch_size,
        args.transfer_mode,
    )

    transfer_provider: Optional[ExportTransferProvider] = None
    if args.transfer_mode == "server":
        transfer_provider = LocalHTTPServerProvider(
            host=args.server_host, port=args.server_port
        )
    elif args.transfer_mode == "tunnelmole":
        transfer_provider = TunnelmoleTransferProvider(
            host=args.server_host, port=args.server_port
        )
    else:
        transfer_provider = ClipboardTransferProvider()

    try:
        controller = ApplicationController(
            config=settings, transfer_provider=transfer_provider
        )
        controller.export_collection(dry_run=args.dry_run)
        logger.info("MTGA Registrar completed successfully.")
        return 0
    except MTGARegistrarError as e:
        logger.error(f"MTGA Registrar failed with domain error: {e}")
        if e.details:
            logger.error(f"Details: {e.details}")
        return 1
    except Exception as e:
        logger.error(
            f"MTGA Registrar failed with unexpected error: {e}", exc_info=True
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
