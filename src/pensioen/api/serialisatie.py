"""Serialisatiehulpen voor API-responses."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel


def naar_json_compatibel(waarde: Any) -> Any:
    """Zet domeinobjecten om naar JSON-compatibele waarden."""
    if is_dataclass(waarde):
        return naar_json_compatibel(asdict(waarde))

    if isinstance(waarde, BaseModel):
        return naar_json_compatibel(waarde.model_dump(mode="json"))

    if isinstance(waarde, Decimal):
        return str(waarde)

    if isinstance(waarde, (date, datetime)):
        return waarde.isoformat()

    if isinstance(waarde, Enum):
        return waarde.value

    if isinstance(waarde, dict):
        return {
            str(sleutel): naar_json_compatibel(subwaarde)
            for sleutel, subwaarde in waarde.items()
        }

    if isinstance(waarde, list):
        return [naar_json_compatibel(item) for item in waarde]

    if isinstance(waarde, tuple):
        return [naar_json_compatibel(item) for item in waarde]

    return waarde
