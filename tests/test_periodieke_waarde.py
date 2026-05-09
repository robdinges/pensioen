"""Tests voor de generieke perioderesolver."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pensioen.models.component import BedragPeriode, BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.periodieke_waarde import PeriodiekeWaarde, get_waarde_op_datum


def test_overlap_meest_recente_start_wint() -> None:
    perioden = [
        PeriodiekeWaarde(waarde=Decimal("36.97"), startdatum=date(2025, 1, 1), einddatum=date(2026, 12, 31)),
        PeriodiekeWaarde(waarde=Decimal("37.48"), startdatum=date(2026, 1, 1), einddatum=date(2030, 12, 31)),
    ]

    assert get_waarde_op_datum(perioden, date(2026, 6, 1)) == Decimal("37.48")


def test_hiaat_laatst_bekende_waarde_blijft_geldig() -> None:
    perioden = [
        PeriodiekeWaarde(waarde=Decimal("10"), startdatum=date(2025, 1, 1), einddatum=date(2025, 12, 31)),
        PeriodiekeWaarde(waarde=Decimal("12"), startdatum=date(2027, 1, 1), einddatum=date(2027, 12, 31)),
    ]

    assert get_waarde_op_datum(perioden, date(2026, 6, 1)) == Decimal("10")


def test_open_einddatum_blijft_doorlopen() -> None:
    perioden = [
        PeriodiekeWaarde(waarde=Decimal("100"), startdatum=date(2025, 1, 1), einddatum=None),
    ]

    assert get_waarde_op_datum(perioden, date(2035, 1, 1)) == Decimal("100")


def test_open_startdatum_geldt_vanaf_begin() -> None:
    perioden = [
        PeriodiekeWaarde(waarde=Decimal("50"), startdatum=None, einddatum=date(2026, 12, 31)),
        PeriodiekeWaarde(waarde=Decimal("60"), startdatum=date(2027, 1, 1), einddatum=None),
    ]

    assert get_waarde_op_datum(perioden, date(2024, 1, 1)) == Decimal("50")


def test_default_wordt_teruggegeven_als_er_nog_geen_waarde_is() -> None:
    perioden = [
        PeriodiekeWaarde(waarde=Decimal("50"), startdatum=date(2025, 1, 1), einddatum=date(2025, 12, 31)),
    ]

    assert get_waarde_op_datum(perioden, date(2024, 1, 1), default=Decimal("0")) == Decimal("0")


def test_financieel_component_meerdere_periodes_selecteert_actieve_waarde() -> None:
    component = FinancieelComponent(
        omschrijving="Salaris",
        categorie=CategorieComponent.ARBEIDSINKOMEN,
        persoon="P1",
        bedrag=Decimal("1000"),
        bedrag_type=BedragType.BRUTO,
        frequentie=Frequentie.MAANDELIJKS,
        waarde_periodes=[
            BedragPeriode(bedrag=Decimal("1000"), startdatum=date(2025, 1, 1), einddatum=date(2025, 12, 31)),
            BedragPeriode(bedrag=Decimal("1500"), startdatum=date(2026, 1, 1), einddatum=None),
        ],
    )

    assert component.bedrag_per_maand_actief(2025, 6) == Decimal("1000")
    assert component.bedrag_per_maand_actief(2026, 6) == Decimal("1500")


def test_financieel_component_groei_start_per_periode_opnieuw() -> None:
    component = FinancieelComponent(
        omschrijving="Huur",
        categorie=CategorieComponent.UITGAVE,
        persoon="Huishouden",
        bedrag=Decimal("1200"),
        bedrag_type=BedragType.NETTO,
        frequentie=Frequentie.JAARLIJKS,
        groei_pct=Decimal("10"),
        waarde_periodes=[
            BedragPeriode(bedrag=Decimal("1200"), startdatum=date(2025, 1, 1), einddatum=date(2029, 12, 31)),
            BedragPeriode(bedrag=Decimal("2400"), startdatum=date(2030, 1, 1), einddatum=None),
        ],
    )

    assert component.bedrag_per_maand_actief(2026, 1) == Decimal("110")
    assert component.bedrag_per_maand_actief(2031, 1) == Decimal("220")