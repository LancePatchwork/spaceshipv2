from dataclasses import dataclass


@dataclass
class EngineConfig:
    tick_hz: int = 2
    save_seed: int = 123


@dataclass
class Paths:
    snapshots_dir: str = "data/snapshots"
    saves_dir: str = "data/saves"
