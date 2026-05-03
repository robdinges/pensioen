"""Tests voor de pensioenengine: pro-rata berekeningen."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.calculations.pensioen_engine import (
    bereken_aow_maand,
    bereken_arbeid_maand,
    bereken_pensioen_maand,
)
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen


class TestBerekenPensioenMaand:
    """Tests voor de pro-rata pensioenberekening per maand."""

    def test_pensioen_start_midden_september(
        self, pensioenrecord_september_start: PensioenRecord
    ) -> None:
        """
        Testcase R1: Pensioen start op 17 september.
        September heeft 30 dagen, resterende dagen = 30 - 17 + 1 = 14.
        Maandbedrag = 12000/12 * (14/30) = 1000 * 0.4667 ≈ 466.67
        """
        record = pensioenrecord_september_start  # ingangsdatum 17 sept 2031
        bedrag = bereken_pensioen_maand(record, 2031, 9)
        verwacht = Decimal("1000") * Decimal("14") / Decimal("30")
        assert float(bedrag) == pytest.approx(float(verwacht), rel=1e-3)

    def test_pensioen_volledig_lopende_maand(
        self, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Een volledig lopende maand geeft 1/12 van het jaarbedrag."""
        record = pensioenrecord_p1  # ingangsdatum 1 jan 2030
        bedrag = bereken_pensioen_maand(record, 2030, 6)
        # Na 0.5 jaar indexatie (2% per jaar, pro-rata niet van toepassing hier)
        # Verwacht: 18400 / 12 ≈ 1533.33
        assert float(bedrag) == pytest.approx(float(Decimal("18400") / Decimal("12")), rel=1e-3)

    def test_pensioen_nog_niet_ingegaan(
        self, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Maand vóór ingangsdatum geeft €0."""
        record = pensioenrecord_p1  # ingangsdatum 1 jan 2030
        assert bereken_pensioen_maand(record, 2029, 12) == Decimal("0")

    def test_pensioen_al_gestopt(self) -> None:
        """Maand na einddatum geeft €0."""
        record = PensioenRecord(
            uitvoerder="Test",
            regeling="Test regeling",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=date(2030, 1, 1),
            einddatum=date(2040, 12, 31),
            bruto_per_jaar=Decimal("12000"),
        )
        assert bereken_pensioen_maand(record, 2041, 1) == Decimal("0")

    def test_partner_pensioen_niet_meegeteld(self) -> None:
        """Partnerpensioen (type PARTNER) telt niet mee als eigen inkomen."""
        record = PensioenRecord(
            uitvoerder="Test",
            regeling="Partnerpensioen",
            type_pensioen=TypePensioen.PARTNER,
            ingangsdatum=date(2030, 1, 1),
            bruto_per_jaar=Decimal("10000"),
        )
        assert bereken_pensioen_maand(record, 2031, 6) == Decimal("0")

    def test_indexatie_na_10_jaar(
        self, pensioenrecord_p1: PensioenRecord
    ) -> None:
        """Na 10 jaar met 2% indexatie is het bedrag hoger dan het beginbedrag."""
        record = pensioenrecord_p1  # 18400/jaar, 2% indexatie, start 2030
        bedrag_start = bereken_pensioen_maand(record, 2030, 6)
        bedrag_10jr = bereken_pensioen_maand(record, 2040, 6)
        assert bedrag_10jr > bedrag_start

    def test_stoppen_halverwege_maand(self) -> None:
        """Einddatum halverwege de maand geeft pro-rata bedrag."""
        record = PensioenRecord(
            uitvoerder="Test",
            regeling="Test",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=date(2030, 1, 1),
            einddatum=date(2035, 6, 15),  # stopt op 15 juni 2035
            bruto_per_jaar=Decimal("12000"),
        )
        bedrag = bereken_pensioen_maand(record, 2035, 6)
        # Juni 2035: einddatum = 15 juni → 15/30 van de maand
        verwacht = Decimal("1000") * Decimal("15") / Decimal("30")
        assert float(bedrag) == pytest.approx(float(verwacht), rel=1e-3)


class TestBerekenAowMaand:
    """Tests voor de AOW pro-rata maandberekening."""

    def test_aow_niet_ingegaan(self) -> None:
        """AOW-datum in de toekomst → €0."""
        geboortedatum = date(1963, 3, 15)
        aow_datum = date(2030, 3, 15)
        bedrag = bereken_aow_maand(
            geboortedatum, aow_datum, Decimal("978"), 2029, 12
        )
        assert bedrag == Decimal("0")

    def test_aow_volledig_lopend(self) -> None:
        """AOW volledig van kracht → vol maandbedrag."""
        geboortedatum = date(1963, 3, 15)
        aow_datum = date(2030, 3, 15)
        bedrag = bereken_aow_maand(
            geboortedatum, aow_datum, Decimal("978"), 2031, 1
        )
        assert bedrag == Decimal("978")

    def test_aow_start_pro_rata(self) -> None:
        """AOW start op 15 september → 16/30 van het maandbedrag."""
        geboortedatum = date(1963, 9, 15)
        aow_datum = date(2030, 9, 15)
        bedrag = bereken_aow_maand(
            geboortedatum, aow_datum, Decimal("978"), 2030, 9
        )
        # 30 - 15 + 1 = 16 dagen van 30
        verwacht = Decimal("978") * Decimal("16") / Decimal("30")
        assert float(bedrag) == pytest.approx(float(verwacht), rel=1e-3)


class TestBerekenArbeidMaand:
    """Tests voor de arbeidsinkomsten pro-rata per maand."""

    def test_stoppen_halverwege_jaar(self) -> None:
        """
        Testcase R10: Stoppen op 15 juni.
        Juni heeft 30 dagen: gewerkte dagen = 15 → 15/30 = 0.5 van de maand.
        """
        salaris = Decimal("60000")
        stopdatum = date(2025, 6, 15)
        bedrag = bereken_arbeid_maand(salaris, stopdatum, 2025, 6)
        maand_salaris = salaris / Decimal("12")
        verwacht = maand_salaris * Decimal("15") / Decimal("30")
        assert float(bedrag) == pytest.approx(float(verwacht), rel=1e-3)

    def test_na_stopdatum_geen_inkomen(self) -> None:
        """Na de stopdatum is het arbeidsinkomen €0."""
        bedrag = bereken_arbeid_maand(Decimal("60000"), date(2025, 6, 1), 2025, 7)
        assert bedrag == Decimal("0")

    def test_voor_stopdatum_vol_salaris(self) -> None:
        """Maand vóór stopdatum geeft volledig maandsalaris."""
        bedrag = bereken_arbeid_maand(Decimal("60000"), date(2025, 6, 1), 2025, 5)
        assert float(bedrag) == pytest.approx(float(Decimal("60000") / Decimal("12")), rel=1e-4)
