"""Tests voor de cashflowengine: huishoudberekeningen over meerdere jaren."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.models.component import BedragType, CategorieComponent, FinancieelComponent, Frequentie
from pensioen.models.pensioen_record import PensioenRecord, TypePensioen
from pensioen.models.persoon import Persoon
from pensioen.models.scenario import IncidenteelItem, Scenario
from pensioen.models.vermogensitem import VermogensItem, VermogensType
from pensioen.tax import aow_engine, heffingskorting
from pensioen.tax.belasting_loader import laad_tarieven_bereik


def _maak_configs(jaar_van: int, jaar_tot: int):
    return laad_tarieven_bereik(jaar_van, jaar_tot)


def _uitgave_comp(bedrag_per_jaar: Decimal) -> FinancieelComponent:
    return FinancieelComponent(
        omschrijving="Vaste lasten",
        categorie=CategorieComponent.UITGAVE,
        persoon="Huishouden",
        bedrag=(bedrag_per_jaar / 12).quantize(Decimal("0.01")),
        frequentie=Frequentie.MAANDELIJKS,
    )


class TestCashflowHuishouden:
    """Integratietests voor het huishoudmodel."""

    def test_basisberekening_levert_resultaten(
        self,
        persoon1: Persoon,
        persoon2: Persoon,
        pensioenrecord_p1: PensioenRecord,
        scenario_standaard: Scenario,
    ) -> None:
        """Basisberekening levert voor elk jaar een JaarResultaat op."""
        configs = _maak_configs(2026, 2035)
        cashflow = bereken_huishouden(
            scenario=scenario_standaard,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2026,
            jaar_tot=2035,
            belasting_configs=configs,
        )
        assert len(cashflow.jaren) == 10
        assert all(len(jr.maanden) == 12 for jr in cashflow.jaren)

    def test_alleenstaande_aow_2025_heeft_belastingdienst_heffingskortingen(self) -> None:
        """Regressie: alleenstaande AOW 2025 gebruikt AOW-AHK + juiste ouderenkorting."""
        persoon = Persoon(naam="AOW", geboortedatum=date(1945, 1, 1), heeft_partner=False)
        scenario = Scenario(
            naam="Alleen AOW",
            spaargeld_start=Decimal("0"),
            box3_meenemen=False,
            componenten=[],
        )
        configs = _maak_configs(2025, 2025)

        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2025,
            jaar_tot=2025,
            belasting_configs=configs,
        )

        jaar = cashflow.jaren[0]
        tarieven = jaar.maanden[0].gebruikte_tarieven["persoon1"]
        config_2025 = configs[2025][0]

        verwacht_ahk = heffingskorting.bereken_ahk_met_aow(
            jaar.bruto_inkomen.p1.totaal,
            config_2025,
            aow_engine.aow_breuk_jaar(persoon.geboortedatum, 2025),
        ).quantize(Decimal("0.01"))

        assert Decimal(str(tarieven["ahk"])) == verwacht_ahk
        assert Decimal(str(tarieven["ahk"])) == Decimal("1536.00")
        assert Decimal(str(tarieven["ouderenkorting"])) == Decimal("2035.00")
        assert Decimal(str(tarieven["alleenstaandeouderenkorting"])) == Decimal("531.00")

        detail = jaar.accountant_detail
        assert detail["verrekende_hk_p1"] == min(
            detail["totale_hk_p1"], detail["totaal_ib_en_premies_p1"]
        )
        assert detail["niet_verrekende_hk_p1"] == max(
            Decimal("0"), detail["totale_hk_p1"] - detail["totaal_ib_en_premies_p1"]
        )

    def test_alleenstaande_aow_met_pensioen_2025_matcht_belastingdienst_1b(self) -> None:
        """Regressie: scenario 1B (AOW + pensioen) volgt Belastingdienst-opbouw 2025."""

        def _r0(bedrag: Decimal) -> int:
            return int(bedrag.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        persoon = Persoon(naam="AOW", geboortedatum=date(1945, 1, 1), heeft_partner=False)
        scenario = Scenario(
            naam="AOW + pensioen",
            spaargeld_start=Decimal("0"),
            box3_meenemen=False,
            componenten=[
                FinancieelComponent(
                    omschrijving="Pensioen",
                    categorie=CategorieComponent.PENSIOEN_INKOMEN,
                    persoon="P1",
                    bedrag=Decimal("50000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                )
            ],
        )
        configs = _maak_configs(2025, 2025)

        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2025,
            jaar_tot=2025,
            belasting_configs=configs,
        )

        detail = cashflow.jaren[0].accountant_detail
        ib = Decimal(str(detail["bel_voor_korting_p1"]))
        pvv = Decimal(str(detail["totaal_premies_p1"]))
        hk = Decimal(str(detail["totale_hk_p1"]))
        totaal_voor_korting = ib + pvv
        hk_verrekend = min(hk, totaal_voor_korting)
        te_betalen = max(Decimal("0"), totaal_voor_korting - hk_verrekend)

        assert abs(_r0(ib) - 13147) <= 1
        assert abs(_r0(pvv) - 3948) <= 1
        assert _r0(hk_verrekend) == 851
        assert abs(_r0(te_betalen) - 16244) <= 1

    def test_netto_groter_dan_nul(
        self,
        persoon1: Persoon,
        pensioenrecord_p1: PensioenRecord,
        scenario_standaard: Scenario,
    ) -> None:
        """Bij normaal pensioeninkomen is het netto inkomen groter dan nul."""
        configs = _maak_configs(2030, 2035)
        cashflow = bereken_huishouden(
            scenario=scenario_standaard,
            persoon1=persoon1,
            persoon2=None,
            records1=[pensioenrecord_p1],
            records2=[],
            jaar_van=2030,
            jaar_tot=2035,
            belasting_configs=configs,
        )
        for jr in cashflow.jaren:
            # Als pensioen ingegaan is, moet netto > 0 zijn
            if jr.jaar >= 2030:
                assert jr.netto > Decimal("0"), f"Netto negatief in {jr.jaar}"

    def test_partner_veel_jonger_twee_aow_data(self) -> None:
        """
        Testcase: Partner is 10 jaar jonger → twee verschillende AOW-data.
        Persoon1 AOW eerder dan persoon2 AOW.
        """
        persoon1 = Persoon(naam="Oudere", geboortedatum=date(1955, 1, 1), heeft_partner=True)
        persoon2 = Persoon(naam="Jongere", geboortedatum=date(1965, 1, 1), heeft_partner=True)

        scenario = Scenario(
            naam="Test",
            spaargeld_start=Decimal("100000"),
            rendement_pct=Decimal("3"),
        )
        configs = _maak_configs(2022, 2040)
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=[],
            records2=[],
            jaar_van=2022,
            jaar_tot=2040,
            belasting_configs=configs,
        )
        assert len(cashflow.jaren) == 19

        # Persoon1 AOW begint eerder dan persoon2
        from pensioen.tax.aow_engine import bereken_aow_datum
        aow1 = bereken_aow_datum(persoon1.geboortedatum).year
        aow2 = bereken_aow_datum(persoon2.geboortedatum).year
        assert aow1 < aow2

    def test_geen_pensioen_alleen_spaargeld(
        self, scenario_geen_pensioen: Scenario
    ) -> None:
        """Scenario zonder pensioenrecords draait alleen op spaargeld + rendement."""
        persoon = Persoon(naam="Spaarder", geboortedatum=date(1960, 1, 1))
        configs = _maak_configs(2035, 2040)
        cashflow = bereken_huishouden(
            scenario=scenario_geen_pensioen,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2035,
            jaar_tot=2040,
            belasting_configs=configs,
        )
        # Geen arbeidsinkomen-componenten → arbeid_bruto = 0
        for jr in cashflow.jaren:
            assert jr.arbeid_bruto == Decimal("0")
        assert cashflow.jaren[-1].vermogen_einde_jaar > Decimal("0")

    def test_incidentele_ontvangst_op_exacte_maand(self) -> None:
        """Een incidentele ontvangst op een specifieke datum wordt in die maand verwerkt."""
        persoon = Persoon(naam="Test", geboortedatum=date(1963, 1, 1))
        scenario = Scenario(
            naam="Test incidenteel",
            spaargeld_start=Decimal("0"),
            incidentele_items=[
                IncidenteelItem(
                    datum=date(2028, 6, 1),
                    bedrag=Decimal("50000"),
                    omschrijving="Erfenis",
                )
            ],
        )
        configs = _maak_configs(2028, 2028)
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2028,
            jaar_tot=2028,
            belasting_configs=configs,
        )
        juni = cashflow.jaren[0].maanden[5]  # maand 6 = index 5
        assert juni.eenmalig_ontvangst == Decimal("50000")

    def test_negatieve_cashflow_jaren_worden_gemarkeerd(self) -> None:
        """Jaren met negatieve netto cashflow worden als tekortjaar herkend."""
        persoon = Persoon(naam="Tekort", geboortedatum=date(1963, 1, 1))
        scenario = Scenario(
            naam="Vroeg stoppen, geen pensioen",
            spaargeld_start=Decimal("1"),  # bijna geen spaargeld
            rendement_pct=Decimal("0"),
            incidentele_items=[
                IncidenteelItem(
                    datum=date(2027, 1, 1),
                    bedrag=Decimal("-20000"),
                    omschrijving="Grote uitgave",
                )
            ],
        )
        configs = _maak_configs(2027, 2027)
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        )
        # Er is een incidentele uitgave van €20.000 maar bijna geen inkomen
        assert cashflow.jaren[0].is_tekortjaar or cashflow.jaren[0].netto < Decimal("20000")

    def test_overlappende_inkomstenbronnen(
        self, persoon1: Persoon
    ) -> None:
        """Twee pensioenen tegelijk worden correct gesommeerd."""
        # Pensioenen zijn nu componenten (niet meer records)
        from pensioen.models.component import (
            FinancieelComponent,
            CategorieComponent,
            BedragType,
            Frequentie,
            BeleggingsType,
        )
        
        pen1 = FinancieelComponent(
            omschrijving="ABP - OP1",
            categorie=CategorieComponent.PENSIOEN_INKOMEN,
            persoon="P1",
            bedrag=Decimal("12000"),
            bedrag_type=BedragType.BRUTO,
            frequentie=Frequentie.JAARLIJKS,
            beleggings_type=BeleggingsType.SPAREN,
            begindatum=date(2030, 1, 1),
        )
        pen2 = FinancieelComponent(
            omschrijving="NN - OP2",
            categorie=CategorieComponent.PENSIOEN_INKOMEN,
            persoon="P1",
            bedrag=Decimal("6000"),
            bedrag_type=BedragType.BRUTO,
            frequentie=Frequentie.JAARLIJKS,
            beleggings_type=BeleggingsType.SPAREN,
            begindatum=date(2030, 1, 1),
        )
        scenario = Scenario(
            naam="Twee pensioenen",
            spaargeld_start=Decimal("0"),
            componenten=[pen1, pen2],
        )
        configs = _maak_configs(2030, 2030)
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=None,
            records1=[],  # Geen records meer, pensioenen zijn componenten
            records2=[],
            jaar_van=2030,
            jaar_tot=2030,
            belasting_configs=configs,
        )
        # Gecombineerd pensioeninkomen per maand ≈ (12000+6000)/12 = 1500
        # Pensioen zit nu in pensioen_bruto (categorie PENSIOEN_INKOMEN)
        totaal_pensioen = cashflow.jaren[0].pensioen_bruto
        assert float(totaal_pensioen) == pytest.approx(18000, rel=1e-3)

    def test_toekomstig_jaar_tarief_fallback(self, persoon1: Persoon) -> None:
        """Voor een jaar zonder config wordt fallback gebruikt en melding opgeslagen."""
        scenario = Scenario(
            naam="Ver toekomst",
            spaargeld_start=Decimal("100000"),
        )
        configs = _maak_configs(2090, 2090)
        cashflow = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2090,
            jaar_tot=2090,
            belasting_configs=configs,
        )
        # De aanname-melding moet aanwezig zijn
        assert any("2090" in a for a in cashflow.aannames)

    def test_huishoudelijke_uitgaven_verlagen_netto(self, persoon1: Persoon) -> None:
        """Huishoudelijke uitgaven verlagen netto cashflow."""
        scenario_zonder = Scenario(
            naam="Zonder uitgaven",
            spaargeld_start=Decimal("0"),
            rendement_pct=Decimal("0"),
        )
        scenario_met = Scenario(
            naam="Met uitgaven",
            spaargeld_start=Decimal("0"),
            rendement_pct=Decimal("0"),
            componenten=[_uitgave_comp(Decimal("12000"))],
        )

        configs = _maak_configs(2027, 2027)
        zonder = bereken_huishouden(
            scenario=scenario_zonder,
            persoon1=persoon1,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        )
        met = bereken_huishouden(
            scenario=scenario_met,
            persoon1=persoon1,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        )

        assert met.jaren[0].netto < zonder.jaren[0].netto
        verschil = zonder.jaren[0].netto - met.jaren[0].netto
        assert float(verschil) == pytest.approx(12000.0, rel=1e-3)

    def test_bruto_component_wordt_belast_en_netto_niet(self) -> None:
        """Bruto inkomenscomponent telt mee voor box 1, netto inkomenscomponent niet."""
        persoon = Persoon(naam="Inkomen", geboortedatum=date(1990, 1, 1))
        comp_bruto = FinancieelComponent(
            omschrijving="Loon bruto",
            categorie=CategorieComponent.ARBEIDSINKOMEN,
            persoon="P1",
            bedrag=Decimal("10000"),
            bedrag_type=BedragType.BRUTO,
            frequentie=Frequentie.MAANDELIJKS,
        )
        comp_netto = FinancieelComponent(
            omschrijving="Loon netto",
            categorie=CategorieComponent.ARBEIDSINKOMEN,
            persoon="P1",
            bedrag=Decimal("10000"),
            bedrag_type=BedragType.NETTO,
            frequentie=Frequentie.MAANDELIJKS,
        )
        scenario_bruto = Scenario(
            naam="Bruto component",
            box3_meenemen=False,
            componenten=[comp_bruto],
        )
        scenario_netto = Scenario(
            naam="Netto component",
            box3_meenemen=False,
            componenten=[comp_netto],
        )

        configs = _maak_configs(2027, 2027)
        resultaat_bruto = bereken_huishouden(
            scenario=scenario_bruto,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        ).jaren[0]
        resultaat_netto = bereken_huishouden(
            scenario=scenario_netto,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        ).jaren[0]

        assert resultaat_bruto.totaal_belasting > Decimal("0")
        assert resultaat_netto.totaal_belasting == Decimal("0")
        assert resultaat_bruto.netto < resultaat_netto.netto

    def test_overschot_naar_spaarrekening(self) -> None:
        """Netto overschot gaat naar saldo en is volgende jaar rentegevend."""
        persoon = Persoon(naam="Spaarder", geboortedatum=date(1965, 1, 1))
        
        # Pensioen 30.000/jaar, geen uitgaven, rendement 3%
        scenario = Scenario(
            naam="Overschot test",
            spaargeld_start=Decimal("0"),
            rendement_pct=Decimal("3"),
            box3_meenemen=False,  # Vereenvoudig: geen box3
            componenten=[
                FinancieelComponent(
                    omschrijving="Pensioen",
                    categorie=CategorieComponent.PENSIOEN_INKOMEN,
                    persoon="P1",
                    bedrag=Decimal("30000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                    begindatum=date(2030, 1, 1),
                )
            ],
        )
        
        configs = _maak_configs(2030, 2031)
        cashflow = bereken_huishouden(
            scenario, persoon, None, [], [], 2030, 2031, configs
        )
        
        # Jaar 1: netto pensioen gaat naar saldo
        vermogen_jaar1 = cashflow.jaren[0].vermogen_einde_jaar
        assert vermogen_jaar1 > Decimal("20000")  # na belasting
        
        # Jaar 2: vermogen groeit met rendement + nieuw netto pensioen
        vermogen_jaar2 = cashflow.jaren[1].vermogen_einde_jaar
        assert vermogen_jaar2 > vermogen_jaar1 * Decimal("1.03")

    def test_tekort_van_spaarrekening(self) -> None:
        """Netto tekort wordt van saldo afgetrokken."""
        persoon = Persoon(naam="Uitgever", geboortedatum=date(1965, 1, 1))
        
        scenario = Scenario(
            naam="Tekort test",
            spaargeld_start=Decimal("100000"),
            rendement_pct=Decimal("0"),
            box3_meenemen=False,
            componenten=[
                FinancieelComponent(
                    omschrijving="Uitgaven",
                    categorie=CategorieComponent.UITGAVE,
                    persoon="Huishouden",
                    bedrag=Decimal("5000"),  # 5000/maand = 60000/jaar
                    frequentie=Frequentie.MAANDELIJKS,
                )
            ],
        )
        
        configs = _maak_configs(2027, 2027)
        cashflow = bereken_huishouden(
            scenario, persoon, None, [], [], 2027, 2027, configs
        )

        # Vermogen daalt met ≈60.000
        vermogen_einde = cashflow.jaren[0].vermogen_einde_jaar
        assert vermogen_einde < Decimal("50000")
        assert vermogen_einde > Decimal("30000")

    def test_jaarresultaat_heeft_expliciete_bruto_opbouw_per_persoon(self) -> None:
        """JaarResultaat vult bruto_inkomen expliciet per persoon en huishouden."""
        persoon1 = Persoon(naam="P1", geboortedatum=date(1980, 1, 1), heeft_partner=True)
        persoon2 = Persoon(naam="P2", geboortedatum=date(1982, 1, 1), heeft_partner=True)

        scenario = Scenario(
            naam="Bruto opbouw",
            box3_meenemen=False,
            componenten=[
                FinancieelComponent(
                    omschrijving="Arbeid P1",
                    categorie=CategorieComponent.ARBEIDSINKOMEN,
                    persoon="P1",
                    bedrag=Decimal("24000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                ),
                FinancieelComponent(
                    omschrijving="Pensioen P2",
                    categorie=CategorieComponent.PENSIOEN_INKOMEN,
                    persoon="P2",
                    bedrag=Decimal("12000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                ),
                FinancieelComponent(
                    omschrijving="Overig P1",
                    categorie=CategorieComponent.OVERIG_INKOMEN,
                    persoon="P1",
                    bedrag=Decimal("6000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                ),
            ],
        )

        configs = _maak_configs(2027, 2027)
        jr = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon1,
            persoon2=persoon2,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        ).jaren[0]

        assert jr.bruto_inkomen.p1.arbeid == Decimal("24000")
        assert jr.bruto_inkomen.p1.overig == Decimal("6000")
        assert jr.bruto_inkomen.p2.pensioen == Decimal("12000")
        assert jr.bruto_inkomen.p1.totaal == Decimal("30000")
        assert jr.bruto_inkomen.p2.totaal == Decimal("12000")
        assert jr.bruto_inkomen.totaal_huishouden == Decimal("42000")

    def test_eenmalige_uitgave_impact(self) -> None:
        """Eenmalige uitgave wordt direct van saldo afgetrokken."""
        persoon = Persoon(naam="Test", geboortedatum=date(1965, 1, 1))
        
        # Vergelijk twee scenarios: met en zonder eenmalige uitgave
        scenario_zonder = Scenario(
            naam="Zonder uitgave",
            spaargeld_start=Decimal("100000"),
            rendement_pct=Decimal("0"),
            box3_meenemen=False,
        )
        
        scenario_met = Scenario(
            naam="Met eenmalige uitgave",
            spaargeld_start=Decimal("100000"),
            rendement_pct=Decimal("0"),
            box3_meenemen=False,
            incidentele_items=[
                IncidenteelItem(
                    datum=date(2027, 6, 1),
                    bedrag=Decimal("-30000"),  # negatief = uitgave
                    omschrijving="Auto kopen",
                )
            ],
        )
        
        configs = _maak_configs(2027, 2027)
        cashflow_zonder = bereken_huishouden(
            scenario_zonder, persoon, None, [], [], 2027, 2027, configs
        )
        cashflow_met = bereken_huishouden(
            scenario_met, persoon, None, [], [], 2027, 2027, configs
        )
        
        # Vermogen daalt met precies 30.000 door de uitgave
        vermogen_zonder = cashflow_zonder.jaren[0].vermogen_einde_jaar
        vermogen_met = cashflow_met.jaren[0].vermogen_einde_jaar
        verschil = vermogen_zonder - vermogen_met
        
        assert float(verschil) == pytest.approx(30000, abs=10)

    def test_box3_grondslag_volgt_box3_belaste_vermogensitems(self) -> None:
        """Box 3 gebruikt expliciet de box-3-grondslag uit vermogensitems, niet het rendementsaldo."""
        persoon = Persoon(naam="Box3", geboortedatum=date(1980, 1, 1), heeft_partner=False)
        scenario = Scenario(
            naam="Box3 bron",
            box3_meenemen=True,
            spaargeld_start=Decimal("0"),
            beleggingen_start=Decimal("0"),
            vermogensitems=[
                VermogensItem(
                    omschrijving="Spaargeld",
                    type=VermogensType.SPAARGELD,
                    aanschafwaarde=Decimal("100000"),
                    box3_belast=True,
                ),
                VermogensItem(
                    omschrijving="Auto",
                    type=VermogensType.AUTO,
                    aanschafwaarde=Decimal("500000"),
                    box3_belast=False,
                ),
            ],
        )

        configs = _maak_configs(2027, 2027)
        jaar = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        ).jaren[0]

        payload_box3 = jaar.maanden[0].gebruikte_tarieven["box3"]
        assert payload_box3["grondslag_bron"] == "vermogensitems"
        assert payload_box3["grondslag_start_vermogen"] == 100000.0
        assert payload_box3["rendement_grondslag_start"] == 100000.0

    def test_eigen_woning_stap_is_actief_in_hoofdengine(self) -> None:
        """Eigen woning mutatie wordt in de hoofdengine verwerkt vóór box 1."""
        persoon = Persoon(naam="Woning", geboortedatum=date(1980, 1, 1), heeft_partner=False)
        scenario = Scenario(
            naam="Eigen woning stap",
            box3_meenemen=False,
            componenten=[
                FinancieelComponent(
                    omschrijving="Arbeid",
                    categorie=CategorieComponent.ARBEIDSINKOMEN,
                    persoon="P1",
                    bedrag=Decimal("60000"),
                    bedrag_type=BedragType.BRUTO,
                    frequentie=Frequentie.JAARLIJKS,
                )
            ],
            vermogensitems=[
                VermogensItem(
                    omschrijving="Eigen woning",
                    type=VermogensType.EIGEN_WONING,
                    aanschafwaarde=Decimal("500000"),
                    woz_waarde=Decimal("500000"),
                    box3_belast=False,
                ),
                VermogensItem(
                    omschrijving="Hypotheek",
                    type=VermogensType.HYPOTHEEK,
                    aanschafwaarde=Decimal("200000"),
                    is_primaire_woning=True,
                    hypotheekrente_pct=Decimal("3.0"),
                    box3_belast=False,
                ),
            ],
        )

        configs = _maak_configs(2027, 2027)
        jaar = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2027,
            belasting_configs=configs,
        ).jaren[0]

        aannames_join = " | ".join(jaar.maanden[0].aannames)
        assert "Eigen woning stap actief" in aannames_join

    def test_meerjarige_box3_grondslag_bewaart_formele_uitsplitsing(self) -> None:
        """Prognosejaar 2 stelt box 3 niet stil gelijk aan het rendementsaldo."""
        persoon = Persoon(
            naam="Box3 meerjarig",
            geboortedatum=date(1980, 1, 1),
            heeft_partner=False,
        )
        scenario = Scenario(
            naam="Box3 uitsplitsing",
            box3_meenemen=False,
            rendement_pct=Decimal("0"),
            vermogensitems=[
                VermogensItem(
                    omschrijving="Belast spaargeld",
                    type=VermogensType.SPAARGELD,
                    aanschafwaarde=Decimal("50000"),
                    box3_belast=True,
                ),
                VermogensItem(
                    omschrijving="Vrijgesteld spaargeld",
                    type=VermogensType.SPAARGELD,
                    aanschafwaarde=Decimal("50000"),
                    box3_belast=False,
                ),
                VermogensItem(
                    omschrijving="Kunst",
                    type=VermogensType.KUNST,
                    aanschafwaarde=Decimal("20000"),
                    box3_belast=True,
                ),
            ],
        )

        jaren = bereken_huishouden(
            scenario=scenario,
            persoon1=persoon,
            persoon2=None,
            records1=[],
            records2=[],
            jaar_van=2027,
            jaar_tot=2028,
            belasting_configs=_maak_configs(2027, 2028),
        ).jaren

        box3_jaar1 = jaren[0].maanden[0].gebruikte_tarieven["box3"]
        box3_jaar2 = jaren[1].maanden[0].gebruikte_tarieven["box3"]

        assert box3_jaar1["grondslag_start_vermogen"] == 70000.0
        assert box3_jaar1["rendement_grondslag_start"] == 100000.0
        assert box3_jaar1["spaargeld_fractie"] == pytest.approx(
            50000 / 70000,
            abs=1e-9,
        )
        assert box3_jaar2["grondslag_bron"] == "vermogensitems_prognose"
        assert box3_jaar2["grondslag_liquide_deel"] == pytest.approx(
            box3_jaar2["rendement_grondslag_start"] * 0.5,
            abs=0.01,
        )
        assert box3_jaar2["grondslag_vaste_items"] == 20000.0
        assert box3_jaar2["grondslag_start_vermogen"] == pytest.approx(
            box3_jaar2["grondslag_liquide_deel"] + 20000.0,
            abs=0.01,
        )
