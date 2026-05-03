"""Datamodel voor een persoon (deelnemer aan de pensioenplanning)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, field_validator


class Persoon(BaseModel):
    """Persoon die deelneemt aan de pensioenplanning."""

    naam: str
    geboortedatum: date
    heeft_partner: bool = False
    partner_id: str | None = None

    @field_validator("geboortedatum")
    @classmethod
    def valideer_geboortedatum(cls, v: date) -> date:
        """Controleer of de geboortedatum binnen een realistisch bereik valt."""
        if not (date(1930, 1, 1) <= v <= date(2010, 12, 31)):
            raise ValueError(
                f"Geboortedatum {v} valt buiten verwacht bereik (1930–2010)."
            )
        return v

    @property
    def geboortejaar(self) -> int:
        return self.geboortedatum.year
