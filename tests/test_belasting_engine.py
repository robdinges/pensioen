"""Tests voor de belastingengine: box 1 berekening en heffingskortingen."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pensioen.tax.belasting_engine import (
    BelastingResultaat,
    bereken_box1_belasting,
    bereken_box3_heffing,
    netto_uit_bruto,
)
from pensioen.tax.belasting_loader import laad_tarieven


class TestBerekenBox1:
    """Tests voor de box 1 belastingberekening."""

    def test_box1_enkelvoudig_schijf1(self) -> None:
        """Inkomen volledig in schijf 1 (niet-AOW)."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("30000"), config=config, aow_breuk=Decimal("0")
        )
        verwacht = Decimal("30000") * Decimal("0.3575")
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_twee_schijven(self) -> None:
        """Inkomen in twee schijven (2026: grens €38.883)."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("50000"), config=config, aow_breuk=Decimal("0")
        )
        verwacht = (
            Decimal("38883") * Decimal("0.3575")
            + Decimal("11117") * Decimal("0.3756")
        )
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_drie_schijven(self) -> None:
        """Inkomen in alle drie schijven."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("100000"), config=config, aow_breuk=Decimal("0")
        )
        verwacht = (
            Decimal("38883") * Decimal("0.3575")
            + (Decimal("78426") - Decimal("38883")) * Decimal("0.3756")
            + (Decimal("100000") - Decimal("78426")) * Decimal("0.4950")
        )
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_aow_gerechtigd_heel_jaar(self) -> None:
        """AOW-tarief schijf 1 is lager dan niet-AOW tarief."""
        config, _ = laad_tarieven(2026)
        belasting_niet_aow = bereken_box1_belasting(
            Decimal("30000"), config, Decimal("0")
        )
        belasting_aow = bereken_box1_belasting(
            Decimal("30000"), config, Decimal("1")
        )
        assert belasting_aow < belasting_niet_aow

    def test_box1_aow_breuk_50_procent(self) -> None:
        """Gewogen belasting bij 50% AOW-breuk zit tussen beide extremen."""
        config, _ = laad_tarieven(2026)
        bel_0 = bereken_box1_belasting(Decimal("30000"), config, Decimal("0"))
        bel_1 = bereken_box1_belasting(Decimal("30000"), config, Decimal("1"))
        bel_half = bereken_box1_belasting(Decimal("30000"), config, Decimal("0.5"))
        verwacht = (bel_0 + bel_1) / Decimal("2")
        assert float(bel_half) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_nul_inkomen(self) -> None:
        """Belasting bij nul inkomen is nul."""
        config, _ = laad_tarieven(2026)
        assert bereken_box1_belasting(Decimal("0"), config, Decimal("0")) == Decimal("0")

    def test_box1_negatief_inkomen_wordt_nul(self) -> None:
        """Negatief inkomen levert geen belasting op."""
        config, _ = laad_tarieven(2026)
        assert bereken_box1_belasting(Decimal("-100"), config, Decimal("0")) == Decimal("0")


class TestNettoUitBruto:
    """Tests voor de volledige netto-uit-bruto berekening."""

    def test_netto_kleiner_dan_bruto(self) -> None:
        """Netto is altijd kleiner dan of gelijk aan bruto."""
        config, _ = laad_tarieven(2026)
        geboortedatum = date(1970, 1, 1)  # niet AOW-gerechtigd in 2026
        resultaat = netto_uit_bruto(
            bruto=Decimal("50000"),
            arbeidsinkomen=Decimal("0"),
            config=config,
            geboortedatum=geboortedatum,
            jaar=2026,
        )
        assert resultaat.netto <= resultaat.bruto
        assert resultaat.netto > Decimal("0")

    def test_effectief_tarief_is_percentage(self) -> None:
        """Effectief tarief ligt tussen 0% en 100%."""
        config, _ = laad_tarieven(2026)
        geboortedatum = date(1970, 1, 1)
        resultaat = netto_uit_bruto(
            bruto=Decimal("50000"),
            arbeidsinkomen=Decimal("0"),
            config=config,
            geboortedatum=geboortedatum,
            jaar=2026,
        )
        assert Decimal("0") <= resultaat.effectief_tarief <= Decimal("100")

    def test_netto_niet_negatief(self) -> None:
        """Netto inkomen is nooit negatief (heffingskortingen overstijgen geen belasting)."""
        config, _ = laad_tarieven(2026)
        geboortedatum = date(1970, 1, 1)
        resultaat = netto_uit_bruto(
            bruto=Decimal("5000"),  # laag inkomen, korting > belasting
            arbeidsinkomen=Decimal("0"),
            config=config,
            geboortedatum=geboortedatum,
            jaar=2026,
        )
        assert resultaat.netto >= Decimal("0")

    def test_toekomstig_jaar_geeft_aanname_melding(self) -> None:
        """Voor een jaar zonder config wordt een fallback + melding gebruikt."""
        config, melding = laad_tarieven(2099)
        assert melding != ""
        assert "2099" in melding

    def test_transparantie_tarieven_aanwezig(self) -> None:
        """Resultaat bevat informatie over gebruikte tarieven."""
        config, _ = laad_tarieven(2026)
        geboortedatum = date(1970, 1, 1)
        resultaat = netto_uit_bruto(
            bruto=Decimal("40000"),
            arbeidsinkomen=Decimal("0"),
            config=config,
            geboortedatum=geboortedatum,
            jaar=2026,
        )
        assert "belastingjaar" in resultaat.gebruikte_tarieven
        assert "ahk" in resultaat.gebruikte_tarieven


class TestBox3:
    """Tests voor de box 3 heffingsberekening."""

    def test_onder_vrijstelling_geen_heffing(self) -> None:
        """Vermogen onder de vrijstelling levert geen box 3 heffing op."""
        config, _ = laad_tarieven(2026)
        heffing, _ = bereken_box3_heffing(
            spaarsaldo=Decimal("50000"),  # onder vrijstelling van €59.357
            config=config,
            heeft_partner=False,
        )
        assert heffing == Decimal("0")

    def test_boven_vrijstelling_positieve_heffing(self) -> None:
        """Vermogen boven de vrijstelling levert heffing op via forfaitair rendement."""
        config, _ = laad_tarieven(2026)
        # Volledig spaargeld (standaard): forfait 1,5% × belastbaar × 36%
        heffing, disclaimer = bereken_box3_heffing(
            spaarsaldo=Decimal("200000"),
            config=config,
            heeft_partner=False,
            spaargeld_fractie=Decimal("1"),
        )
        belastbaar = Decimal("200000") - config.box3.vrijstelling_per_persoon
        fictief = belastbaar * config.box3.forfaitair_spaargeld
        verwacht = fictief * config.box3.tarief
        assert float(heffing) == pytest.approx(float(verwacht), rel=1e-3)
        assert len(disclaimer) > 0  # disclaimer altijd aanwezig

    def test_dubbele_vrijstelling_met_partner(self) -> None:
        """Met partner is de vrijstelling verdubbeld."""
        config, _ = laad_tarieven(2026)
        heffing_enkel, _ = bereken_box3_heffing(
            Decimal("120000"), config, heeft_partner=False
        )
        heffing_partner, _ = bereken_box3_heffing(
            Decimal("120000"), config, heeft_partner=True
        )
        # Met partner: vrijstelling = 2 × €59.357 = €118.714 → belastbaar €1.286
        # Zonder: vrijstelling = €59.357 → belastbaar €60.643
        assert heffing_partner < heffing_enkel
