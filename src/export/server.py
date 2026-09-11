"""Local HTTP server export and tunneling transfer provider.

This module implements a lightweight local HTTP server (`LocalHTTPServerProvider`)
using standard library `http.server` to receive incoming clipboard/deck data or
server exported decklists when running via GeForce Now sandboxing.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Optional, Tuple, Type

from src.core.exceptions import ExportError
from src.export.base import ExportTransferProvider

logger = logging.getLogger("mtga_registrar")


class _DeckRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for receiving and serving deck/collection data."""

    def log_message(self, format: str, *args: Any) -> None:
        """Override default logging to route through application logger."""
        logger.debug(f"HTTP Server: {format % args}")

    def do_GET(self) -> None:
        """Handle GET requests to retrieve exported data or status."""
        server_provider = typing_cast_server(self.server)
        try:
            if self.path == "/status" or self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response_data = {
                    "status": "active",
                    "has_data": server_provider.exported_data is not None,
                }
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            elif self.path == "/export" or self.path == "/data":
                data = server_provider.exported_data
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                if data:
                    self.wfile.write(data.encode("utf-8"))
                else:
                    self.wfile.write(b"")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_response(500)
            self.end_headers()

    def do_POST(self) -> None:
        """Handle POST requests to receive incoming deck/collection data."""
        server_provider = typing_cast_server(self.server)
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            body_str = body_bytes.decode("utf-8", errors="ignore")

            received_text = body_str
            if self.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    json_data = json.loads(body_str)
                    if isinstance(json_data, dict) and "data" in json_data:
                        received_text = str(json_data["data"])
                    elif isinstance(json_data, str):
                        received_text = json_data
                except json.JSONDecodeError:
                    pass

            server_provider.store_received_data(received_text)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "success", "message": "Data received successfully."}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.info("Successfully received incoming deck data via HTTP POST.")
        except Exception as e:
            logger.error(f"Failed to process POST request: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_response = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(error_response).encode("utf-8"))


class LocalHTTPServer(HTTPServer):
    """Custom HTTPServer that holds references to exported and received data."""

    def __init__(
        self,
        server_address: Tuple[str, int],
        request_handler_class: Type[BaseHTTPRequestHandler],
    ) -> None:
        """Initialize LocalHTTPServer with thread lock and data stores."""
        super().__init__(server_address, request_handler_class)
        self.exported_data: Optional[str] = None
        self.received_data: Optional[str] = None
        self._lock = threading.Lock()

    def store_received_data(self, data: str) -> None:
        """Thread-safely store received data."""
        with self._lock:
            self.received_data = data

    def get_received_data(self) -> Optional[str]:
        """Thread-safely retrieve received data."""
        with self._lock:
            return self.received_data


def typing_cast_server(server_instance: Any) -> LocalHTTPServer:
    """Helper for mypy type casting of HTTP server instance."""
    return server_instance  # type: ignore


class LocalHTTPServerProvider(ExportTransferProvider):
    """Local HTTP server export and tunneling transfer provider."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Initialize the local HTTP server provider.

        Args:
            host: Host interface to bind server to (default: 127.0.0.1).
            port: Port number to listen on (default: 8000).
        """
        self.host = host
        self.port = port
        self.server: Optional[LocalHTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the local HTTP server in a background daemon thread.

        Raises:
            ExportError: If server startup fails.
        """
        if self.server is not None:
            logger.warning("Local HTTP server is already running.")
            return

        try:
            self.server = LocalHTTPServer((self.host, self.port), _DeckRequestHandler)
            self.server_thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.server_thread.start()
            logger.info(f"Local HTTP server started at http://{self.host}:{self.port}")
        except Exception as e:
            logger.error(
                f"Failed to start local HTTP server on {self.host}:{self.port}: {e}"
            )
            raise ExportError(
                f"Failed to start local HTTP server on port {self.port}",
                details=str(e),
            ) from e

    def stop(self) -> None:
        """Stop the local HTTP server and clean up threads."""
        if self.server is not None:
            try:
                self.server.shutdown()
                self.server.server_close()
                if self.server_thread and self.server_thread.is_alive():
                    self.server_thread.join(timeout=2.0)
                logger.info("Local HTTP server stopped.")
            except Exception as e:
                logger.error(f"Error stopping local HTTP server: {e}")
            finally:
                self.server = None
                self.server_thread = None

    def transfer(self, data: str) -> bool:
        """Store deck data on the server to be served or transmitted.

        Args:
            data: The decklist string to publish/serve.

        Returns:
            True if successfully published.

        Raises:
            ExportError: If server is not running or data is invalid.
        """
        if self.server is None:
            raise ExportError("Cannot transfer data: Local HTTP server is not running.")
        try:
            if not isinstance(data, str):
                raise ExportError("Transfer data must be a string.")
            with self.server._lock:
                self.server.exported_data = data
            logger.debug("Successfully published deck data to local HTTP server.")
            return True
        except Exception as e:
            logger.error(f"Failed to transfer/publish data via HTTP server: {e}")
            raise ExportError("HTTP server data transfer failed", details=str(e)) from e

    def get_data(self) -> Optional[str]:
        """Retrieve data received from incoming HTTP POST requests.

        Returns:
            The received data string, or None if none received yet.

        Raises:
            ExportError: If server is not running.
        """
        if self.server is None:
            raise ExportError("Cannot get data: Local HTTP server is not running.")
        return self.server.get_received_data()

    def get_url(self) -> str:
        """Get the base URL of the local server.

        Returns:
            String URL (e.g., http://127.0.0.1:8000).
        """
        return f"http://{self.host}:{self.port}"
