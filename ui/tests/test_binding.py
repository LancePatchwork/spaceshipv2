from __future__ import annotations

from ui.core.binding import to_dashboard_vm


def test_to_dashboard_vm_populates_fields() -> None:
    snap: dict[str, object] = {
        "meta": {"tick": 5, "ts_ms": 100},
        "state": {
            "power": {"plant_kw": 42.0, "plant_max_kw": 100.0},
            "battery": {"kw": 10.0, "capacity_kw": 50.0},
            "life": {
                "o2_pct": 21.0,
                "life_temp_c": 22.0,
                "ship_temp_c": 20.0,
                "crew_awake": 4,
            },
        },
    }

    vm = to_dashboard_vm(snap)
    assert vm["meta"]["tick"] == 5
    assert vm["power"]["plant_kw"] == 42.0
    assert vm["battery"]["capacity_kw"] == 50.0
    assert vm["life"]["crew_awake"] == 4


def test_to_dashboard_vm_defaults_missing_fields() -> None:
    snap: dict[str, object] = {"meta": {}, "state": {}}
    vm = to_dashboard_vm(snap)
    assert vm["meta"]["tick"] == 0
    assert vm["power"]["plant_kw"] == 0.0
    assert vm["battery"]["kw"] == 0.0
    assert vm["life"]["crew_awake"] == 0
