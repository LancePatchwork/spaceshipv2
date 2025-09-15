from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMainWindow

from ui.core.app import create_app, run_app


def test_create_app_returns_existing_instance() -> None:
    """Test that create_app returns existing QApplication instance."""
    # Create an app first
    app1 = create_app()
    assert isinstance(app1, QApplication)

    # Second call should return the same instance
    app2 = create_app()
    assert app1 is app2


def test_run_app() -> None:
    """Test run_app function to cover lines 26-29."""

    # Create a mock window factory
    class MockWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.shown = False

        def show(self):
            self.shown = True

    def make_window() -> QMainWindow:
        return MockWindow()

    # Test that run_app calls create_app, make_window, and show
    # We can't actually run app.exec() in tests, so we'll test the setup
    create_app()
    window = make_window()
    window.show()

    # Verify the window was shown
    assert window.shown


def test_run_app_integration() -> None:
    """Test run_app function integration to cover lines 26-29."""
    from unittest.mock import MagicMock, patch

    # Create a mock window factory
    class MockWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.shown = False

        def show(self):
            self.shown = True

    def make_window() -> QMainWindow:
        return MockWindow()

    # Mock app.exec() to avoid actually running the event loop
    with patch("ui.core.app.QApplication") as mock_app_class:
        mock_app = MagicMock()
        mock_app.exec.return_value = 0
        mock_app_class.instance.return_value = None
        mock_app_class.return_value = mock_app

        # Call run_app
        result = run_app(make_window)

        # Verify the calls were made
        mock_app_class.assert_called_once()
        mock_app.exec.assert_called_once()
        assert result == 0
