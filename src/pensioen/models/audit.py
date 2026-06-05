"""Audit trail datamodellen voor scenario-wijzigingen."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class AuditEntry:
    """Eén wijziging in een scenario (voor audit trail)."""

    timestamp: datetime
    scenario_naam: str
    field_path: str  # dotted path bijv. "rendement_pct" of "componenten.0.bedrag"
    old_value: Any
    new_value: Any
    is_override: bool  # True als dit een override in afgeleid scenario is
    user_process: str = "streamlit"  # gebruiker of proces dat wijziging deed

    def __repr__(self) -> str:
        override_marker = " [OVERRIDE]" if self.is_override else ""
        return (
            f"AuditEntry({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"{self.scenario_naam}, {self.field_path}: "
            f"{self._format_value(self.old_value)} → {self._format_value(self.new_value)}{override_marker})"
        )

    @staticmethod
    def _format_value(value: Any) -> str:
        """Formatteer waarde voor weergave in audit log."""
        if value is None:
            return "None"
        if isinstance(value, Decimal):
            return f"€{float(value):,.2f}" if value != Decimal("0") else "€0.00"
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(value)


@dataclass
class MutationLog:
    """Volledige audit log van alle wijzigingen in scenario's."""

    entries: list[AuditEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_entry(self, entry: AuditEntry) -> None:
        """Voeg een audit entry toe aan de log."""
        self.entries.append(entry)

    def get_entries_for_scenario(
        self, scenario_naam: str, limit: int | None = None
    ) -> list[AuditEntry]:
        """Haal audit entries op voor een specifiek scenario."""
        entries = [e for e in self.entries if e.scenario_naam == scenario_naam]
        # Sorteer reverse chronologisch (nieuwste eerst)
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        if limit is not None:
            return entries[:limit]
        return entries

    def get_entries_for_field(
        self, scenario_naam: str, field_path: str, limit: int | None = None
    ) -> list[AuditEntry]:
        """Haal audit entries op voor een specifiek veld in een scenario."""
        entries = [
            e
            for e in self.entries
            if e.scenario_naam == scenario_naam and e.field_path == field_path
        ]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        if limit is not None:
            return entries[:limit]
        return entries

    def get_recent_entries(self, limit: int = 50) -> list[AuditEntry]:
        """Haal de meest recente audit entries op (cross-scenario)."""
        entries = sorted(self.entries, key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar dictionary voor JSON opslag."""
        return {
            "created_at": self.created_at.isoformat(),
            "entries": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "scenario_naam": e.scenario_naam,
                    "field_path": e.field_path,
                    "old_value": self._serialize_value(e.old_value),
                    "new_value": self._serialize_value(e.new_value),
                    "is_override": e.is_override,
                    "user_process": e.user_process,
                }
                for e in self.entries
            ],
        }

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialiseer waarde voor JSON opslag."""
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        # Lists en dicts worden direct geserializeerd door JSON encoder
        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MutationLog:
        """Deserialiseer vanuit dictionary (geladen uit JSON)."""
        log = cls(created_at=datetime.fromisoformat(data["created_at"]))
        for entry_data in data.get("entries", []):
            entry = AuditEntry(
                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                scenario_naam=entry_data["scenario_naam"],
                field_path=entry_data["field_path"],
                old_value=entry_data["old_value"],
                new_value=entry_data["new_value"],
                is_override=entry_data.get("is_override", False),
                user_process=entry_data.get("user_process", "streamlit"),
            )
            log.add_entry(entry)
        return log
