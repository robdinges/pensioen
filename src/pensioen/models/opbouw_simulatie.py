"""Expliciete aannames of uitvoerdersgegevens voor pensioenopbouw na stoppen."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OpbouwKeuze(BaseModel):
    pensioen_index: int = Field(ge=0)
    laatste_werkdag: date
    doorwerken_tot: date
    pensioen_vanaf: date
    premie_per_maand: Decimal = Field(ge=0, allow_inf_nan=False)
    pensioen_doorwerken: Decimal = Field(ge=0, allow_inf_nan=False)
    pensioen_zonder: Decimal = Field(ge=0, allow_inf_nan=False)
    pensioen_met: Decimal = Field(ge=0, allow_inf_nan=False)
    modus: Literal['aannames', 'uitvoerder'] = 'aannames'
    bron: str = ''
    brondatum: date | None = None

    @model_validator(mode='after')
    def valideer_keuze(self) -> OpbouwKeuze:
        if not self.laatste_werkdag < self.doorwerken_tot < self.pensioen_vanaf:
            raise ValueError('Kies: eerder stoppen vóór doorwerken tot, en doorwerken tot vóór pensioen ingaat.')
        if self.modus == 'uitvoerder' and (not self.bron.strip() or not self.brondatum):
            raise ValueError('Vul bij uitvoerdersgegevens de bron en datum van de berekening in.')
        return self
