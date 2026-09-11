"""Comprehensive unit tests for export transfer providers, clipboard utility,

deck parser, and browser navigation.
Verifies ClipboardTransferProvider, ClipboardUtility, DeckParser, LocalHTTPServerProvider,
TunnelmoleTransferProvider (with subprocess mocking), payload acceptance, server endpoints,
and BrowserController.
"""

import socket
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from src.automation.browser import BrowserController
from src.core.app import ApplicationController
from src.core.exceptions import AutomationError, ExportError
from src.export.base import ClipboardTransferProvider, ExportTransferProvider
from src.export.clipboard import ClipboardUtility
from src.export.parser import DeckParser
from src.export.server import LocalHTTPServerProvider
from src.export.tunnelmole import TunnelmoleTransferProvider


def get_free_port() -> int:
    """Get a free ephemeral port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        return int(port)


def test_clipboard_transfer_provider() -> None:
    """Verify ClipboardTransferProvider transfer, get_data, start, and stop."""
    provider = ClipboardTransferProvider()
    provider.start()

    # Test transfer success
    with patch("pyperclip.copy") as mock_copy:
        assert provider.transfer("Deck: 4 Lightning Bolt") is True
        mock_copy.assert_called_once_with("Deck: 4 Lightning Bolt")

    # Test transfer error
    with patch("pyperclip.copy", side_effect=Exception("Clipboard error")):
        with pytest.raises(ExportError) as exc_info:
            provider.transfer("Bad data")
        assert "System clipboard copy failed" in str(exc_info.value)

    # Test get_data success
    with patch("pyperclip.paste", return_value="Sample deck data"):
        assert provider.get_data() == "Sample deck data"

    # Test get_data error
    with patch("pyperclip.paste", side_effect=Exception("Paste error")):
        with pytest.raises(ExportError) as exc_info:
            provider.get_data()
        assert "System clipboard paste failed" in str(exc_info.value)

    provider.stop()


def test_clipboard_utility_methods() -> None:
    """Verify ClipboardUtility copy, paste, clear, and error handling."""
    with patch("pyperclip.copy") as mock_copy, \
         patch("pyperclip.paste", return_value="Test Text"):
        assert ClipboardUtility.copy("Hello MTGA") is True
        mock_copy.assert_called_once_with("Hello MTGA")

        assert ClipboardUtility.paste() == "Test Text"

        assert ClipboardUtility.clear() is True
        mock_copy.assert_called_with("")

    # Test copy invalid input error
    with pytest.raises(ExportError):
        ClipboardUtility.copy(123)  # type: ignore

    # Test copy exception wrapping
    with patch("pyperclip.copy", side_effect=Exception("Copy failed")):
        with pytest.raises(ExportError) as exc_info:
            ClipboardUtility.copy("Fail")
        assert "System clipboard copy operation failed" in str(exc_info.value)

    # Test paste exception wrapping
    with patch("pyperclip.paste", side_effect=Exception("Paste failed")):
        with pytest.raises(ExportError) as exc_info:
            ClipboardUtility.paste()
        assert "System clipboard paste operation failed" in str(exc_info.value)

    # Test clear exception wrapping
    with patch("pyperclip.copy", side_effect=Exception("Clear failed")):
        with pytest.raises(ExportError) as exc_info:
            ClipboardUtility.clear()
        assert "System clipboard clear operation failed" in str(exc_info.value)


def test_clipboard_utility_wait_for_clipboard() -> None:
    """Verify ClipboardUtility.wait_for_clipboard success and timeout."""
    # Success when content changes
    with patch(
        "pyperclip.paste",
        side_effect=["Initial", "Initial", "New Export Deck"],
    ):
        content = ClipboardUtility.wait_for_clipboard(
            timeout=1.0,
            poll_interval=0.05,
            initial_content="Initial",
        )
        assert content == "New Export Deck"

    # Timeout when content does not change
    with patch("pyperclip.paste", return_value="Stale Content"):
        content = ClipboardUtility.wait_for_clipboard(
            timeout=0.2,
            poll_interval=0.05,
            initial_content="Stale Content",
        )
        assert content is None


def test_deck_parser() -> None:
    """Verify DeckParser correctly parses raw MTGA export text into structured models."""
    sample_text = """
    Deck
    2 Llanowar Elves (FDN) 227
    6 Forest (FIN) 306
    Sideboard
    1 Ugin, Eye of the Storms (TDM) 1
    """

    deck = DeckParser.parse(sample_text)
    assert len(deck.cards) == 3

    # Verify card 1
    c1 = deck.cards[0]
    assert c1.quantity == 2
    assert c1.name == "Llanowar Elves"
    assert c1.set_code == "FDN"
    assert c1.collector_number == "227"
    assert c1.category == "mainboard"

    # Verify card 3 (sideboard)
    c3 = deck.cards[2]
    assert c3.quantity == 1
    assert c3.name == "Ugin, Eye of the Storms"
    assert c3.set_code == "TDM"
    assert c3.collector_number == "1"
    assert c3.category == "sideboard"

    # Verify model serialization
    d_dict = deck.to_dict()
    assert d_dict["total_cards"] == 9
    assert d_dict["unique_cards"] == 3

    d_json = deck.to_json()
    assert "Llanowar Elves" in d_json
    assert "TDM" in d_json


def test_deck_parser_invalid() -> None:
    """Verify DeckParser handling of invalid inputs."""
    with pytest.raises(ExportError):
        DeckParser.parse(123)  # type: ignore

    empty_deck = DeckParser.parse("")
    assert len(empty_deck.cards) == 0


def test_local_http_server_provider() -> None:
    """Verify LocalHTTPServerProvider startup, payload acceptance, GET/POST endpoints, and stop."""
    port = get_free_port()
    server_provider = LocalHTTPServerProvider(host="127.0.0.1", port=port)

    # Before start, transfer / get_data should raise ExportError
    with pytest.raises(ExportError):
        server_provider.transfer("data")
    with pytest.raises(ExportError):
        server_provider.get_data()

    server_provider.start()
    try:
        url = server_provider.get_url()
        assert url == f"http://127.0.0.1:{port}"

        # Test publishing data via transfer()
        test_deck = "1 Plains\\n1 Island"
        assert server_provider.transfer(test_deck) is True

        # Test HTTP GET /status endpoint
        req = urllib.request.Request(f"{url}/status")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            assert resp.status == 200
            body = resp.read().decode("utf-8")
            assert "active" in body
            assert "has_data" in body

        # Test HTTP GET /export endpoint
        req_export = urllib.request.Request(f"{url}/export")
        with urllib.request.urlopen(req_export, timeout=3.0) as resp:
            assert resp.status == 200
            exported_body = resp.read().decode("utf-8")
            assert exported_body == test_deck

        # Test HTTP POST incoming data
        post_data = "Incoming received deck"
        req_post = urllib.request.Request(
            f"{url}/data",
            data=post_data.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        with urllib.request.urlopen(req_post, timeout=3.0) as resp:
            assert resp.status == 200

        # Verify server received data
        assert server_provider.get_data() == post_data

        # Test HTTP GET 404
        req_404 = urllib.request.Request(f"{url}/notfound")
        try:
            urllib.request.urlopen(req_404, timeout=3.0)
        except urllib.error.HTTPError as e:
            assert e.code == 404

    finally:
        server_provider.stop()


def test_tunnelmole_transfer_provider_mocked() -> None:
    """Verify TunnelmoleTransferProvider starts with subprocess mock and acquires public URL."""
    port = get_free_port()
    tmole = TunnelmoleTransferProvider(host="127.0.0.1", port=port, timeout=3.0)

    mock_process = MagicMock()
    mock_process.stdout = [
        "Tunnelmole initializing...\\n",
        "https://test-subdomain-123.tunnelmole.net\\n",
        "Tunnel active\\n",
    ]
    mock_process.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        tmole.start()
        try:
            assert tmole.get_public_url() == "https://test-subdomain-123.tunnelmole.net"
            assert tmole.get_url() == "https://test-subdomain-123.tunnelmole.net"
            mock_popen.assert_called_once()
        finally:
            tmole.stop()


def test_tunnelmole_transfer_provider_timeout() -> None:
    """Verify TunnelmoleTransferProvider raises ExportError on URL acquisition timeout."""
    port = get_free_port()
    tmole = TunnelmoleTransferProvider(host="127.0.0.1", port=port, timeout=0.5)

    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.poll.return_value = None

    with patch("subprocess.Popen", return_value=mock_process):
        with pytest.raises(ExportError) as exc_info:
            tmole.start()
        assert "Timeout" in str(exc_info.value) or "Failed" in str(exc_info.value)


def test_modular_transfer_switching() -> None:
    """Verify polymorphism and switching between standard clipboard and server/tunnel providers."""
    providers: list[ExportTransferProvider] = [
        ClipboardTransferProvider(),
        LocalHTTPServerProvider(port=get_free_port()),
    ]

    for p in providers:
        p.start()
        try:
            if isinstance(p, ClipboardTransferProvider):
                with patch("pyperclip.copy") as mock_copy:
                    p.transfer("test data")
                    mock_copy.assert_called_once()
            elif isinstance(p, LocalHTTPServerProvider):
                p.transfer("server data")
                assert p.server is not None
        finally:
            p.stop()


def test_browser_controller_navigation() -> None:
    """Verify BrowserController navigation with and without address bar coordinates."""
    with patch("src.automation.keyboard.KeyboardController.hotkey") as mock_hotkey, \
         patch("src.automation.keyboard.KeyboardController.type_text") as mock_type, \
         patch("src.automation.keyboard.KeyboardController.press_key") as mock_press, \
         patch("src.automation.mouse.MouseController.click") as mock_click, \
         patch("src.automation.timing.sleep_random", return_value=None):

        # Navigate with URL and no coords (uses Ctrl+L / Alt+D shortcut)
        BrowserController.navigate_to_url("https://my-tunnel.tunnelmole.net")
        mock_hotkey.assert_any_call("ctrl", "l")
        mock_type.assert_called_once_with(
            "https://my-tunnel.tunnelmole.net", interval=0.04
        )
        mock_press.assert_called_once_with("enter")
        mock_click.assert_not_called()

        mock_hotkey.reset_mock()
        mock_type.reset_mock()
        mock_press.reset_mock()

        # Navigate with address bar coordinates
        BrowserController.navigate_to_url(
            "https://another.tunnelmole.net", address_bar_coords=(100, 200)
        )
        mock_click.assert_called_once_with(100, 200)
        mock_type.assert_called_once_with(
            "https://another.tunnelmole.net", interval=0.04
        )


def test_browser_controller_open_help() -> None:
    """Verify BrowserController open_help_link_or_browser with and without coords."""
    with patch("src.automation.mouse.MouseController.click") as mock_click, \
         patch("src.automation.keyboard.KeyboardController.hotkey") as mock_hotkey, \
         patch("src.automation.timing.sleep_random", return_value=None):

        BrowserController.open_help_link_or_browser(click_coords=(50, 50))
        mock_click.assert_called_once_with(50, 50)
        mock_hotkey.assert_not_called()

        BrowserController.open_help_link_or_browser()
        mock_hotkey.assert_called_once_with("ctrl", "shift", "o")


def test_browser_controller_invalid_url() -> None:
    """Verify BrowserController raises AutomationError on invalid URL."""
    with pytest.raises(AutomationError) as exc_info:
        BrowserController.navigate_to_url("ftp://invalid-url.com")
    assert "Invalid URL provided" in str(exc_info.value)


def test_browser_controller_privacy_and_tab_operations() -> None:
    """Verify BrowserController privacy and tab operations."""
    with patch("src.automation.keyboard.KeyboardController.press_key") as mock_press, \
         patch("src.automation.mouse.MouseController.click") as mock_click, \
         patch("src.automation.keyboard.KeyboardController.hotkey") as mock_hotkey, \
         patch("src.automation.keyboard.KeyboardController.type_text") as mock_type, \
         patch("src.automation.timing.sleep_random", return_value=None):

        BrowserController.open_privacy_browser(click_coords=(100, 100))
        mock_press.assert_any_call("esc")
        mock_click.assert_called_with(100, 100)

        BrowserController.open_privacy_browser()
        mock_click.assert_called_with(960, 900)

        BrowserController.navigate_and_transfer("https://test.tunnelmole.net")
        mock_hotkey.assert_any_call("ctrl", "l")
        mock_type.assert_called_with("https://test.tunnelmole.net", interval=0.04)

        BrowserController.close_current_tab()
        mock_hotkey.assert_called_with("ctrl", "w")


def test_application_controller_deck_cleanup() -> None:
    """Verify ApplicationController save_current_deck and export_and_cleanup_deck."""
    app = ApplicationController()
    with patch("src.vision.capture.ScreenCapture.capture_screen", return_value=MagicMock()), \
         patch("src.vision.ui.UIDetector.find_confirmation_ok_button",
               return_value=(10, 10, 50, 20)), \
         patch("src.vision.ui.UIDetector.find_decks_search_bar",
               return_value=(20, 20, 100, 30)), \
         patch("src.vision.ui.UIDetector.find_leftmost_deck",
               return_value=(30, 30, 150, 200)), \
         patch("src.vision.ui.UIDetector.find_export_button",
               return_value=(40, 40, 100, 40)), \
         patch("src.vision.ui.UIDetector.find_trash_can_button",
               return_value=(50, 50, 40, 40)), \
         patch("src.automation.mouse.MouseController.click") as mock_click, \
         patch("src.automation.keyboard.KeyboardController.hotkey") as mock_hotkey, \
         patch("src.automation.keyboard.KeyboardController.type_text") as mock_type, \
         patch("src.automation.keyboard.KeyboardController.press_key") as mock_press, \
         patch("src.automation.timing.sleep_random", return_value=None):

        app.save_current_deck()
        mock_click.assert_called()

        app.export_and_cleanup_deck()
        mock_hotkey.assert_any_call("ctrl", "a")
        mock_type.assert_called_with("New Deck", interval=0.04)
        mock_press.assert_called_with("enter")


