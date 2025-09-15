from __future__ import annotations

from textual.widgets import Static

from ui.windows.dashboard_tui import DashboardTUI


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, interval_ms: int = 1000):
        self.interval_ms = interval_ms
        self._snapshots = []
        self._current_index = 0

    def add_snapshot(self, snapshot: dict) -> None:
        """Add a snapshot to the provider."""
        self._snapshots.append(snapshot)

    def get_latest(self) -> dict | None:
        """Get the latest snapshot."""
        if not self._snapshots:
            return None
        return self._snapshots[-1]


def test_dashboard_tui_initialization() -> None:
    """Test DashboardTUI initialization."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    assert app._provider is provider
    assert isinstance(app._status, Static)
    assert isinstance(app._plant, Static)
    assert isinstance(app._battery, Static)
    assert isinstance(app._o2, Static)
    assert isinstance(app._life_temp, Static)
    assert isinstance(app._ship_temp, Static)
    assert isinstance(app._tick, Static)


def test_dashboard_tui_compose() -> None:
    """Test DashboardTUI compose method."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    widgets = list(app.compose())
    assert len(widgets) == 7
    assert widgets[0] is app._status
    assert widgets[1] is app._plant
    assert widgets[2] is app._battery
    assert widgets[3] is app._o2
    assert widgets[4] is app._life_temp
    assert widgets[5] is app._ship_temp
    assert widgets[6] is app._tick


def test_dashboard_tui_on_mount() -> None:
    """Test DashboardTUI on_mount method."""
    provider = MockProvider(interval_ms=500)
    app = DashboardTUI(provider)

    # on_mount should set an interval, but we can't test it without an event loop
    # So we'll just test that the method exists and can be called
    # The actual interval setting requires a running Textual app
    assert hasattr(app, "on_mount")


def test_dashboard_tui_on_mount_with_mock() -> None:
    """Test DashboardTUI on_mount method with mocked set_interval to cover line 35."""
    from unittest.mock import patch

    provider = MockProvider(interval_ms=1000)
    app = DashboardTUI(provider)

    # Mock set_interval to avoid event loop issues
    with patch.object(app, "set_interval") as mock_set_interval:
        app.on_mount()

        # Verify set_interval was called with correct parameters
        mock_set_interval.assert_called_once_with(1.0, app._refresh)  # 1000ms / 1000 = 1.0s


def test_dashboard_tui_refresh_no_data() -> None:
    """Test DashboardTUI _refresh method with no data."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    # Initial state
    app._status.update("Initial")
    app._plant.update("Initial Plant")
    app._battery.update("Initial Battery")
    app._o2.update("Initial O2")
    app._life_temp.update("Initial Life Temp")
    app._ship_temp.update("Initial Ship Temp")
    app._tick.update("Initial Tick")

    # Refresh with no data
    app._refresh()

    # Should show waiting message and clear other widgets
    assert app._status.content == "Waiting for data..."
    assert app._plant.content == ""
    assert app._battery.content == ""
    assert app._o2.content == ""
    assert app._life_temp.content == ""
    assert app._ship_temp.content == ""
    assert app._tick.content == ""


def test_dashboard_tui_refresh_with_data() -> None:
    """Test DashboardTUI _refresh method with data."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    # Add a snapshot with data
    snapshot = {
        "meta": {"tick": 42},
        "state": {
            "power": {"plant_output_kw": 150.5, "battery_kw": 75.25, "battery_capacity_kw": 100.0},
            "life": {"o2_pct": 21.5, "life_temp_c": 22.3},
            "env": {"ship_temp_c": 20.1},
        },
    }
    provider.add_snapshot(snapshot)

    # Refresh with data
    app._refresh()

    # Should update all widgets with data
    assert app._status.content == ""
    assert app._plant.content == "Plant Output: 150.5 kW"
    assert app._battery.content == "Battery: 75.2 / 100.0 kW"
    assert app._o2.content == "O2: 21.5%"
    assert app._life_temp.content == "Life Temp: 22.3 °C"
    assert app._ship_temp.content == "Ship Temp: 20.1 °C"
    assert app._tick.content == "Tick: 42"


def test_dashboard_tui_refresh_missing_fields() -> None:
    """Test DashboardTUI _refresh method with missing fields."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    # Add a snapshot with minimal data
    snapshot = {"meta": {"tick": 1}, "state": {}}
    provider.add_snapshot(snapshot)

    # Refresh with minimal data
    app._refresh()

    # Should use default values for missing fields
    assert app._status.content == ""
    assert app._plant.content == "Plant Output: 0.0 kW"
    assert app._battery.content == "Battery: 0.0 / 0.0 kW"
    assert app._o2.content == "O2: 0.0%"
    assert app._life_temp.content == "Life Temp: 0.0 °C"
    assert app._ship_temp.content == "Ship Temp: 0.0 °C"
    assert app._tick.content == "Tick: 1"


def test_dashboard_tui_refresh_partial_data() -> None:
    """Test DashboardTUI _refresh method with partial data."""
    provider = MockProvider()
    app = DashboardTUI(provider)

    # Add a snapshot with partial data
    snapshot = {
        "meta": {"tick": 10},
        "state": {
            "power": {
                "plant_output_kw": 50.0
                # Missing battery data
            },
            "life": {
                "o2_pct": 20.0
                # Missing temperature data
            },
            # Missing env data
        },
    }
    provider.add_snapshot(snapshot)

    # Refresh with partial data
    app._refresh()

    # Should use provided data and defaults for missing fields
    assert app._status.content == ""
    assert app._plant.content == "Plant Output: 50.0 kW"
    assert app._battery.content == "Battery: 0.0 / 0.0 kW"
    assert app._o2.content == "O2: 20.0%"
    assert app._life_temp.content == "Life Temp: 0.0 °C"
    assert app._ship_temp.content == "Ship Temp: 0.0 °C"
    assert app._tick.content == "Tick: 10"
