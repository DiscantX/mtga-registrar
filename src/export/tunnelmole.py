"""Tunnelmole process management and public URL tunneling provider.

This module implements `TunnelmoleTransferProvider`, which combines a local HTTP server
(`LocalHTTPServerProvider`) with the Tunnelmole (`tmole`) CLI tunneling tool to expose
a local endpoint as a public `https://*.tunnelmole.net` URL for data transfer in
sandboxed environments like GeForce Now.
"""

import logging
import re
import subprocess
import threading
from typing import Optional

from src.core.exceptions import ExportError
from src.export.server import LocalHTTPServerProvider

logger = logging.getLogger("mtga_registrar")


class TunnelmoleTransferProvider(LocalHTTPServerProvider):
    """Transfer provider using a local HTTP server tunneled via Tunnelmole (`tmole`)."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        tmole_binary: str = "tmole",
        timeout: float = 15.0,
    ) -> None:
        """Initialize the Tunnelmole transfer provider.

        Args:
            host: Local host interface for the HTTP server (default: 127.0.0.1).
            port: Local port number to listen on and tunnel (default: 5000).
            tmole_binary: Path or command name for tmole executable (default: "tmole").
            timeout: Maximum seconds to wait for public URL acquisition
                from tmole stdout (default: 15.0).
        """
        super().__init__(host=host, port=port)
        self.tmole_binary = tmole_binary
        self.timeout = timeout
        self.process: Optional[subprocess.Popen[str]] = None
        self.public_url: Optional[str] = None
        self._url_event = threading.Event()

    def start(self) -> None:
        """Start the local HTTP server and the Tunnelmole tunneling subprocess.

        Raises:
            ExportError: If server startup or tmole tunneling fails.
        """
        # Start local HTTP server first
        super().start()

        try:
            cmd = [self.tmole_binary, str(self.port)]
            logger.info(f"Starting Tunnelmole subprocess: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            self._url_event.clear()
            self.public_url = None

            # Start background thread to read tmole output and parse public URL
            reader_thread = threading.Thread(
                target=self._read_tmole_output, args=(self.process,), daemon=True
            )
            reader_thread.start()

            # Wait for public URL acquisition
            if not self._url_event.wait(timeout=self.timeout):
                self.stop()
                raise ExportError(
                    f"Timeout ({self.timeout}s) waiting for Tunnelmole public URL acquisition."
                )

            if not self.public_url:
                self.stop()
                raise ExportError("Failed to extract public URL from Tunnelmole process output.")

            logger.info(f"Tunnelmole tunnel established at: {self.public_url}")

        except Exception as e:
            self.stop()
            if isinstance(e, ExportError):
                raise
            logger.error(f"Failed to start Tunnelmole transfer provider: {e}")
            raise ExportError(
                "Failed to start Tunnelmole process or acquire tunneling URL",
                details=str(e),
            ) from e

    def _read_tmole_output(self, process: subprocess.Popen[str]) -> None:
        """Read stdout from tmole subprocess to extract the tunnelmole.net public URL.

        Args:
            process: The active tmole subprocess handle.
        """
        url_pattern = re.compile(r"https://[a-zA-Z0-9.-]+\.tunnelmole\.net")
        try:
            if process.stdout:
                for line in process.stdout:
                    stripped = line.strip()
                    logger.debug(f"tmole output: {stripped}")
                    match = url_pattern.search(stripped)
                    if match:
                        self.public_url = match.group(0)
                        self._url_event.set()
                        break
        except Exception as e:
            logger.error(f"Error reading Tunnelmole output stream: {e}")

    def stop(self) -> None:
        """Stop the Tunnelmole subprocess and shut down the local HTTP server."""
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3.0)
                logger.info("Tunnelmole subprocess terminated.")
            except subprocess.TimeoutExpired:
                logger.warning("Tunnelmole process did not terminate gracefully, killing...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping Tunnelmole process: {e}")
            finally:
                self.process = None

        self.public_url = None
        super().stop()

    def get_public_url(self) -> Optional[str]:
        """Retrieve the acquired public Tunnelmole URL.

        Returns:
            The public https://*.tunnelmole.net URL string, or None if not running.
        """
        return self.public_url

    def get_url(self) -> str:
        """Get the active tunnel public URL or fallback to local URL.

        Returns:
            Public tunnel URL if active, otherwise local HTTP URL.
        """
        if self.public_url:
            return self.public_url
        return super().get_url()
