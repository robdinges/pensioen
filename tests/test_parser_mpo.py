"""Tests voor de parser en validator van MijnPensioenoverzicht-exports."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pensioen.models.pensioen_record import TypePensioen
from pensioen.parsers.parser_mpo import MPOParser
from pensioen.validators.validator import valideer_records


class TestMPOParser:
    """Tests voor het inlezen van CSV-exports."""

    def test_parse_csv_fictief_bestand(self, fixture_dir: Path) -> None:
        """Leest het fictieve testbestand correct in."""
        records = MPOParser.parse_csv(fixture_dir / "mpo_partner1.csv")
        assert len(records) == 2
        assert records[0].uitvoerder == "ABP"
        assert records[0].bruto_per_jaar == Decimal("18400")
        assert records[0].type_pensioen == TypePensioen.OUDERDOMS
        assert records[0].ingangsdatum == date(2030, 1, 1)

    def test_parse_csv_partner2(self, fixture_dir: Path) -> None:
        """Leest het fixture-bestand van partner 2 in."""
        records = MPOParser.parse_csv(fixture_dir / "mpo_partner2.csv")
        assert len(records) == 1
        assert records[0].uitvoerder == "Pensioenfonds Zorg en Welzijn"
        assert records[0].ingangsdatum == date(2035, 4, 1)

    def test_parse_csv_onbekende_kolommen_worden_genegeerd(
        self, tmp_path: Path
    ) -> None:
        """Onbekende kolomnamen mogen het parsen niet verstoren."""
        inhoud = (
            "uitvoerder,regeling,type_pensioen,ingangsdatum,bruto_per_jaar,onbekend\n"
            "Test BV,Test regeling,ouderdoms,2030-01-01,10000,xyz\n"
        )
        bestand = tmp_path / "test.csv"
        bestand.write_text(inhoud, encoding="utf-8")
        records = MPOParser.parse_csv(bestand)
        assert len(records) == 1

    def test_parse_csv_lege_einddatum_wordt_none(self, fixture_dir: Path) -> None:
        """Een lege einddatum-kolom resulteert in None (niet een fout)."""
        records = MPOParser.parse_csv(fixture_dir / "mpo_partner1.csv")
        assert all(r.einddatum is None for r in records)

    def test_auto_parse_detecteert_csv(self, fixture_dir: Path) -> None:
        """De .parse()-methode detecteert CSV op basis van extensie."""
        records = MPOParser.parse(fixture_dir / "mpo_partner1.csv")
        assert len(records) > 0

    def test_onbekende_extensie_geeft_fout(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Onbekende bestandsextensie"):
            MPOParser.parse(tmp_path / "bestand.txt")


class TestValidator:
    """Tests voor de validatielogica."""

    def test_geldig_record(self, pensioenrecord_p1) -> None:
        """Een correct record passeert validatie zonder fouten."""
        resultaat = valideer_records([pensioenrecord_p1])
        assert resultaat.is_geldig
        assert len(resultaat.fouten) == 0

    def test_negatief_bedrag(self) -> None:
        """Negatief bruto bedrag is een FOUT."""
        from pensioen.models.pensioen_record import PensioenRecord

        with pytest.raises(Exception):
            # Pydantic validator gooit al een fout bij negatief bedrag
            PensioenRecord(
                uitvoerder="Test",
                regeling="Test",
                type_pensioen=TypePensioen.OUDERDOMS,
                ingangsdatum=date(2030, 1, 1),
                bruto_per_jaar=Decimal("-1000"),
            )

    def test_ontbrekende_uitvoerder(self) -> None:
        """Lege uitvoerder geeft een FOUT in de validator."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="",
            regeling="Test",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=date(2030, 1, 1),
            bruto_per_jaar=Decimal("10000"),
        )
        resultaat = valideer_records([record])
        assert not resultaat.is_geldig
        fout_velden = [f.veld for f in resultaat.fouten]
        assert "uitvoerder" in fout_velden

    def test_onrealistisch_hoog_bedrag_is_waarschuwing(self) -> None:
        """Bedrag boven €500.000 geeft een WAARSCHUWING (geen FOUT)."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="Test",
            regeling="Test",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=date(2030, 1, 1),
            bruto_per_jaar=Decimal("600000"),
        )
        resultaat = valideer_records([record])
        assert resultaat.is_geldig  # geen fouten
        assert any(w.ernst == "WAARSCHUWING" for w in resultaat.waarschuwingen)

    def test_duplicaat_geeft_waarschuwing(self) -> None:
        """Twee identieke records geven een WAARSCHUWING."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="ABP",
            regeling="OP",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=date(2030, 1, 1),
            bruto_per_jaar=Decimal("18400"),
        )
        resultaat = valideer_records([record, record])
        assert any(w.ernst == "WAARSCHUWING" for w in resultaat.waarschuwingen)

    def test_lege_lijst_is_waarschuwing(self) -> None:
        """Een lege lijst records geeft een WAARSCHUWING."""
        resultaat = valideer_records([])
        assert not resultaat.is_geldig or len(resultaat.waarschuwingen) > 0
