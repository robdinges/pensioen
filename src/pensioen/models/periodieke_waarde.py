"""Gedeelde perioderesolutie voor tijdsafhankelijke waarden."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence


@dataclass(frozen=True, slots=True)
class PeriodiekeWaarde:
    """Een waarde die geldig is binnen een optionele datumperiode."""

    waarde: Decimal
    startdatum: date | None = None
    einddatum: date | None = None


def _startsleutel(datum: date | None) -> date:
    return datum if datum is not None else date.min


def _eindsleutel(datum: date | None) -> date:
    return datum if datum is not None else date.max


def _is_actief(periodieke_waarde: PeriodiekeWaarde, peildatum: date) -> bool:
    if periodieke_waarde.startdatum is not None and peildatum < periodieke_waarde.startdatum:
        return False
    if periodieke_waarde.einddatum is not None and peildatum > periodieke_waarde.einddatum:
        return False
    return True


def _selectiesleutel(periodieke_waarde: PeriodiekeWaarde) -> tuple[date, date]:
    return (_startsleutel(periodieke_waarde.startdatum), _eindsleutel(periodieke_waarde.einddatum))


def selecteer_periodieke_waarde(
    perioden: Sequence[PeriodiekeWaarde],
    peildatum: date,
) -> PeriodiekeWaarde | None:
    """Selecteer de geldige periode voor een datum.

    Regels:
    - actieve periodes winnen van inactieve periodes;
    - bij overlap wint de meest recente startdatum;
    - bij een hiaat blijft de laatst bekende waarde gelden;
    - als er nog geen eerdere waarde is, wordt None teruggegeven.
    """
    periode_lijst = list(perioden)
    if not periode_lijst:
        return None

    actieve_periodes = [p for p in periode_lijst if _is_actief(p, peildatum)]
    if actieve_periodes:
        return max(actieve_periodes, key=_selectiesleutel)

    bekende_verleden = [
        p for p in periode_lijst
        if p.startdatum is None or p.startdatum <= peildatum
    ]
    if bekende_verleden:
        return max(bekende_verleden, key=_selectiesleutel)

    return None


def get_waarde_op_datum(
    perioden: Sequence[PeriodiekeWaarde],
    peildatum: date,
    default: Decimal | None = None,
) -> Decimal | None:
    """Geef de geldige waarde terug op een peildatum."""
    geselecteerd = selecteer_periodieke_waarde(perioden, peildatum)
    if geselecteerd is None:
        return default
    return geselecteerd.waarde