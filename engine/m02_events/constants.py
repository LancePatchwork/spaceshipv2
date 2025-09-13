from __future__ import annotations

from typing import Final

Category = str //test
Scope = str

CATEGORIES: Final[set[Category]] = {
    "bridge",
    "engineering",
    "medical",
    "security",
    "navigation",
    "ops",
    "damage_control",
    "crew_admin",
    "alerts",
    "environment",
    "comms",
}

SCOPES: Final[set[Scope]] = {
    "captain",
    "officers",
    "shipwide",
    "department:engineering",
    "department:medical",
    "department:security",
    "department:bridge",
    "department:ops",
    "private:<actor_id>",
    "rank:<name>",
    "crew:<role>",
}

__all__ = ["Category", "Scope", "CATEGORIES", "SCOPES"]
