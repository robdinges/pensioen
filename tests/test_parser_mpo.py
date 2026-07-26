"""Tests voor de parser en validator van MijnPensioenoverzicht-exports."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.pensioen_record import TypePensioen
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import Scenario
from pensioen.parsers.parser_mpo import MPOParser, pensioenrecords_naar_rekencomponenten
from pensioen.tax.belasting_loader import laad_tarieven
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

    def test_pensioenrecords_naar_rekencomponenten_filtert_op_ouderdoms(self) -> None:
        """Transformatielaag neemt standaard alleen ouderdomspensioen op."""
        from pensioen.models.pensioen_record import PensioenRecord

        records = [
            PensioenRecord(
                uitvoerder="Fonds A",
                regeling="OP",
                type_pensioen=TypePensioen.OUDERDOMS,
                ingangsdatum=date(2030, 1, 1),
                bruto_per_jaar=Decimal("12000"),
            ),
            PensioenRecord(
                uitvoerder="Fonds A",
                regeling="PP",
                type_pensioen=TypePensioen.PARTNER,
                ingangsdatum=None,
                bruto_per_jaar=Decimal("5000"),
            ),
        ]

        componenten = pensioenrecords_naar_rekencomponenten(records, persoon="P1")

        assert len(componenten) == 1
        assert componenten[0].persoon == "P1"
        assert componenten[0].categorie.value == "pensioen_inkomen"
        assert componenten[0].bedrag == Decimal("12000")

    def test_pensioenrecords_naar_rekencomponenten_met_explicit_type_set(self) -> None:
        """Transformatielaag kan expliciet partnerpensioen meenemen als dat gevraagd wordt."""
        from pensioen.models.pensioen_record import PensioenRecord

        records = [
            PensioenRecord(
                uitvoerder="Fonds B",
                regeling="PP",
                type_pensioen=TypePensioen.PARTNER,
                ingangsdatum=None,
                bruto_per_jaar=Decimal("7000"),
            )
        ]

        componenten = pensioenrecords_naar_rekencomponenten(
            records,
            persoon="P2",
            toegestane_types={TypePensioen.PARTNER},
        )

        assert len(componenten) == 1
        assert componenten[0].persoon == "P2"
        assert "Partnerpensioen" in componenten[0].omschrijving

    def test_mpo_transformatie_is_enige_pensioenbron_voor_huishouden(
        self, fixture_dir: Path
    ) -> None:
        """Meerdere MPO-records voor P1 en P2 lopen via componenten naar de engine."""
        records1 = MPOParser.parse_csv(fixture_dir / "mpo_partner1.csv")
        records2 = MPOParser.parse_csv(fixture_dir / "mpo_partner2.csv")
        componenten = [
            *pensioenrecords_naar_rekencomponenten(records1, persoon="P1"),
            *pensioenrecords_naar_rekencomponenten(records2, persoon="P2"),
        ]
        scenario = Scenario(
            naam="MPO naar rekenbron",
            componenten=componenten,
            box3_meenemen=False,
        )
        persoon1 = Persoon(
            naam="P1",
            geboortedatum=date(1965, 1, 1),
            heeft_partner=True,
        )
        persoon2 = Persoon(
            naam="P2",
            geboortedatum=date(1967, 1, 1),
            heeft_partner=True,
        )
        config, aanname = laad_tarieven(2036)

        jaar = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=records1,
            records2=records2,
            jaar_van=2036,
            jaar_tot=2036,
            belasting_configs={2036: (config, aanname)},
        ).jaren[0]

        verwacht_p1 = sum(
            (
                component.bedrag_per_maand_actief(2036, maand)
                for component in componenten
                if component.persoon == "P1"
                for maand in range(1, 13)
            ),
            Decimal("0"),
        )
        verwacht_p2 = sum(
            (
                component.bedrag_per_maand_actief(2036, maand)
                for component in componenten
                if component.persoon == "P2"
                for maand in range(1, 13)
            ),
            Decimal("0"),
        )

        assert jaar.bruto_inkomen.p1.pensioen == verwacht_p1
        assert jaar.bruto_inkomen.p2.pensioen == verwacht_p2
        assert any(
            "PensioenRecord-invoer ontvangen" in aanname
            for aanname in jaar.maanden[0].aannames
        )


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


class TestValidatorEdgeCases:
    """Regressietests voor validator-randgevallen."""

    def test_partner_pensioen_zonder_ingangsdatum_geen_waarschuwing(self) -> None:
        """PARTNER-type zonder ingangsdatum geeft GEEN waarschuwing (ingangsdatum is n.v.t.)."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="Test Fonds",
            regeling="PP-001",
            type_pensioen=TypePensioen.PARTNER,
            ingangsdatum=None,
            bruto_per_jaar=Decimal("10000"),
        )
        resultaat = valideer_records([record])
        ingangsdatum_warns = [
            w for w in resultaat.waarschuwingen if w.veld == "ingangsdatum"
        ]
        assert len(ingangsdatum_warns) == 0

    def test_nabestaanden_pensioen_zonder_ingangsdatum_geen_waarschuwing(self) -> None:
        """NABESTAANDEN-type zonder ingangsdatum geeft GEEN waarschuwing."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="Test Fonds",
            regeling="NP-001",
            type_pensioen=TypePensioen.NABESTAANDEN,
            ingangsdatum=None,
            bruto_per_jaar=Decimal("5000"),
        )
        resultaat = valideer_records([record])
        ingangsdatum_warns = [
            w for w in resultaat.waarschuwingen if w.veld == "ingangsdatum"
        ]
        assert len(ingangsdatum_warns) == 0

    def test_ouderdoms_pensioen_zonder_ingangsdatum_geeft_waarschuwing(self) -> None:
        """OUDERDOMS-type zonder ingangsdatum geeft WEL een WAARSCHUWING."""
        from pensioen.models.pensioen_record import PensioenRecord

        record = PensioenRecord(
            uitvoerder="Test Fonds",
            regeling="OP-001",
            type_pensioen=TypePensioen.OUDERDOMS,
            ingangsdatum=None,
            bruto_per_jaar=Decimal("20000"),
        )
        resultaat = valideer_records([record])
        ingangsdatum_warns = [
            w for w in resultaat.waarschuwingen if w.veld == "ingangsdatum"
        ]
        assert len(ingangsdatum_warns) == 1
        assert ingangsdatum_warns[0].ernst == "WAARSCHUWING"


class TestMPOParserJSON:
    """Tests voor het inlezen van JSON-exports (Stichting Pensioenregister-formaat)."""

    def _schrijf_mpo_json(self, tmp_path: Path, data: dict) -> Path:
        import json

        bestand = tmp_path / "mpo.json"
        bestand.write_text(json.dumps(data), encoding="utf-8")
        return bestand

    def _minimale_json(self) -> dict:
        """Minimale geldige JSON-structuur conform het SPR-datamodel."""
        return {
            "TijdstipAanmakenBericht": "2026-05-03T16:27:43+02:00",
            "Totalen": {},
            "Details": {
                "OuderdomsPensioenDetails": {
                    "OuderdomsPensioen": [
                        {
                            "Van": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                            "Tot": {"OuderdomsPensioenEvent": "Overlijden"},
                            "Pensioen": [
                                {
                                    "TeBereiken": 41457,
                                    "Opgebouwd": 41457,
                                    "PensioenUitvoerder": "St. Pensioenfonds F. van Lanschot",
                                    "HerkenningsNummer": "0000001375-1",
                                    "StandPer": "2026-03-31",
                                }
                            ],
                        }
                    ]
                },
                "PartnerPensioenDetails": {"PartnerPensioen": []},
                "WezenPensioenDetails": {"WezenPensioen": []},
            },
        }

    def test_parse_json_ouderdomspensioen(self, tmp_path: Path) -> None:
        """Leest een ouderdomspensioenrecord correct in vanuit JSON."""
        bestand = self._schrijf_mpo_json(tmp_path, self._minimale_json())
        records = MPOParser.parse_json(bestand)
        ouderdoms = [r for r in records if r.type_pensioen == TypePensioen.OUDERDOMS]
        assert len(ouderdoms) == 1
        assert ouderdoms[0].uitvoerder == "St. Pensioenfonds F. van Lanschot"
        assert ouderdoms[0].bruto_per_jaar == Decimal("41457")
        assert ouderdoms[0].einddatum is None  # eindigt bij overlijden

    def test_parse_json_ingangsdatum_via_geboortedatum(self, tmp_path: Path) -> None:
        """Ingangsdatum wordt correct afgeleid uit leeftijd + geboortedatum."""
        bestand = self._schrijf_mpo_json(tmp_path, self._minimale_json())
        records = MPOParser.parse_json(bestand, geboortedatum=date(1958, 1, 1))
        ouderdoms = [r for r in records if r.type_pensioen == TypePensioen.OUDERDOMS]
        assert ouderdoms[0].ingangsdatum == date(2026, 1, 1)  # 1958 + 68j0m

    def test_parse_json_ingangsdatum_none_zonder_geboortedatum(self, tmp_path: Path) -> None:
        """Zonder geboortedatum blijft ingangsdatum None."""
        bestand = self._schrijf_mpo_json(tmp_path, self._minimale_json())
        records = MPOParser.parse_json(bestand)
        assert all(r.ingangsdatum is None for r in records if r.type_pensioen == TypePensioen.OUDERDOMS)

    def test_parse_json_partnerpensioen(self, tmp_path: Path) -> None:
        """Partnerpensioen wordt als TypePensioen.PARTNER ingelezen."""
        data = self._minimale_json()
        data["Details"]["PartnerPensioenDetails"] = {
            "PartnerPensioen": [
                {
                    "Van": {"PartnerEvent": "OverlijdenPartner"},
                    "Tot": {"PartnerEvent": "Overlijden"},
                    "Pensioen": [
                        {
                            "Bedragen": {"VerzekerdBedragNaPens": 10242, "VerzekerdBedrag": 5000},
                            "PensioenUitvoerder": "St. Pensioenfonds F. van Lanschot",
                            "HerkenningsNummer": "0000001375-1",
                            "StandPer": "2026-03-31",
                        }
                    ],
                }
            ]
        }
        bestand = self._schrijf_mpo_json(tmp_path, data)
        records = MPOParser.parse_json(bestand)
        partner = [r for r in records if r.type_pensioen == TypePensioen.PARTNER]
        assert len(partner) == 1
        # VerzekerdBedragNaPens heeft voorkeur boven VerzekerdBedrag
        assert partner[0].bruto_per_jaar == Decimal("10242")

    def test_parse_json_meerdere_tijdvakken_deduplicatie(self, tmp_path: Path) -> None:
        """Eén uitvoerder met meerdere tijdvakken levert één record op."""
        data = self._minimale_json()
        data["Details"]["OuderdomsPensioenDetails"]["OuderdomsPensioen"] = [
            {
                "Van": {"Leeftijd": {"Jaren": 65, "Maanden": 0}},
                "Tot": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                "Pensioen": [
                    {
                        "TeBereiken": 515,
                        "Opgebouwd": 515,
                        "PensioenUitvoerder": "AEGON",
                        "HerkenningsNummer": "DLN-001",
                        "StandPer": "2026-03-01",
                    }
                ],
            },
            {
                "Van": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                "Tot": {"OuderdomsPensioenEvent": "Overlijden"},
                "Pensioen": [
                    {
                        "TeBereiken": 515,
                        "Opgebouwd": 515,
                        "PensioenUitvoerder": "AEGON",
                        "HerkenningsNummer": "DLN-001",
                        "StandPer": "2026-03-01",
                    }
                ],
            },
        ]
        bestand = self._schrijf_mpo_json(tmp_path, data)
        records = MPOParser.parse_json(bestand)
        aegon = [r for r in records if r.uitvoerder == "AEGON"]
        assert len(aegon) == 1
        assert aegon[0].einddatum is None  # eindigt bij overlijden

    def test_parse_json_verkiest_toekomstige_pensioenstart(self, tmp_path: Path) -> None:
        """Een historisch opbouwtijdvak mag de toekomstige pensioenstart niet vervangen."""
        data = self._minimale_json()
        pensioen = {
            "TeBereiken": 12000,
            "Opgebouwd": 8000,
            "PensioenUitvoerder": "Testfonds",
            "HerkenningsNummer": "REG-TOEKOMST",
            "StandPer": "2026-03-01",
        }
        data["Details"]["OuderdomsPensioenDetails"]["OuderdomsPensioen"] = [
            {
                "Van": {"Leeftijd": {"Jaren": 47, "Maanden": 0}},
                "Tot": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                "Pensioen": [pensioen],
            },
            {
                "Van": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                "Tot": {"OuderdomsPensioenEvent": "Overlijden"},
                "Pensioen": [pensioen],
            },
        ]

        bestand = self._schrijf_mpo_json(tmp_path, data)
        records = MPOParser.parse_json(bestand, geboortedatum=date(1960, 3, 15))

        assert len(records) == 1
        assert records[0].ingangsdatum == date(2028, 3, 1)

    def test_parse_json_enkel_tijdvak_gebruikt_toekomstige_tot_datum(
        self, tmp_path: Path
    ) -> None:
        """Een historisch Van met toekomstig Tot gebruikt Tot als pensioenmoment."""
        data = self._minimale_json()
        data["Details"]["OuderdomsPensioenDetails"]["OuderdomsPensioen"] = [
            {
                "Van": {"Leeftijd": {"Jaren": 47, "Maanden": 0}},
                "Tot": {"Leeftijd": {"Jaren": 68, "Maanden": 0}},
                "Pensioen": [
                    {
                        "TeBereiken": 12000,
                        "Opgebouwd": 8000,
                        "PensioenUitvoerder": "Testfonds",
                        "HerkenningsNummer": "REG-ENKEL",
                        "StandPer": "2026-03-01",
                    }
                ],
            }
        ]

        bestand = self._schrijf_mpo_json(tmp_path, data)
        records = MPOParser.parse_json(bestand, geboortedatum=date(1960, 3, 15))

        assert len(records) == 1
        assert records[0].ingangsdatum == date(2028, 3, 1)

    def test_parse_json_expliciete_vanafdatum_heeft_voorrang(
        self, tmp_path: Path
    ) -> None:
        """De item-vanafDatum is leidend boven een historisch buitenste tijdvak."""
        data = self._minimale_json()
        data["Details"]["OuderdomsPensioenDetails"]["OuderdomsPensioen"] = [
            {
                "Van": {"Leeftijd": {"Jaren": 47, "Maanden": 0}},
                "Tot": {"OuderdomsPensioenEvent": "Overlijden"},
                "Pensioen": [
                    {
                        "TeBereiken": 12000,
                        "Opgebouwd": 8000,
                        "PensioenUitvoerder": "Testfonds",
                        "HerkenningsNummer": "REG-EXPLICIET",
                        "StandPer": "2026-03-01",
                        "vanafDatum": "2040-04-19",
                        "vanafLeeftijdJaren": 68,
                        "vanafLeeftijdMaanden": 0,
                        "totOverlijden": True,
                    }
                ],
            }
        ]

        bestand = self._schrijf_mpo_json(tmp_path, data)
        records = MPOParser.parse_json(bestand, geboortedatum=date(1972, 4, 19))

        assert len(records) == 1
        assert records[0].ingangsdatum == date(2040, 4, 19)
        assert records[0].einddatum is None

    def test_parse_json_peildatum_uit_bericht(self, tmp_path: Path) -> None:
        """Peildatum wordt afgeleid uit TijdstipAanmakenBericht."""
        bestand = self._schrijf_mpo_json(tmp_path, self._minimale_json())
        records = MPOParser.parse_json(bestand)
        assert all(r.peildatum == date(2026, 5, 3) for r in records)

    def test_auto_parse_detecteert_json(self, tmp_path: Path) -> None:
        """De .parse()-methode detecteert .json op basis van extensie."""
        import json

        bestand = tmp_path / "mpo.json"
        bestand.write_text(json.dumps(self._minimale_json()), encoding="utf-8")
        records = MPOParser.parse(bestand)
        assert len(records) > 0
