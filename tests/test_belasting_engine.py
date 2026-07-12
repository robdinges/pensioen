"""Tests voor de belastingengine: box 1 berekening en heffingskortingen."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pensioen.tax.belasting_engine import (
    BelastingResultaat,
    bereken_box1_belasting,
    bereken_box3_heffing,
    netto_uit_bruto,
)
from pensioen.tax.heffingskorting import bereken_ahk_met_aow
from pensioen.tax import belasting_loader
from pensioen.tax.belasting_loader import (
    laad_tarieven,
    resolve_tariefwaarden_voor_jaar,
    schrijf_belastingconfig_json,
)


class TestBerekenBox1:
    """Tests voor de box 1 belastingberekening."""

    def test_box1_enkelvoudig_schijf1(self) -> None:
        """Inkomen volledig in schijf 1 (niet-AOW)."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("30000"), config=config, aow_breuk=Decimal("0")
        )
        # 2026: pure IB is 8,1% (premies worden apart berekend)
        verwacht = Decimal("30000") * Decimal("0.081")
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_twee_schijven(self) -> None:
        """Inkomen in twee schijven (2026: grens €38.883)."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("50000"), config=config, aow_breuk=Decimal("0")
        )
        # 2026: pure IB tarieven zonder premies
        verwacht = (
            Decimal("38883") * Decimal("0.081")
            + Decimal("11117") * Decimal("0.3756")
        )
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_drie_schijven(self) -> None:
        """Inkomen in alle drie schijven."""
        config, _ = laad_tarieven(2026)
        belasting = bereken_box1_belasting(
            bruto=Decimal("100000"), config=config, aow_breuk=Decimal("0")
        )
        # 2026: pure IB tarieven zonder premies
        verwacht = (
            Decimal("38883") * Decimal("0.081")
            + (Decimal("78426") - Decimal("38883")) * Decimal("0.3756")
            + (Decimal("100000") - Decimal("78426")) * Decimal("0.4950")
        )
        assert float(belasting) == pytest.approx(float(verwacht), rel=1e-3)

    def test_box1_aow_gerechtigd_heel_jaar(self) -> None:
        """In 2026: pure IB is gelijk voor AOW en niet-AOW (8,1%)."""
        config, _ = laad_tarieven(2026)
        belasting_niet_aow = bereken_box1_belasting(
            Decimal("30000"), config, Decimal("0")
        )
        belasting_aow = bereken_box1_belasting(
            Decimal("30000"), config, Decimal("1")
        )
        # Pure IB is nu gelijk, verschil zit in premies (apart berekend)
        assert belasting_aow == belasting_niet_aow

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

    def test_resolve_tariefwaarden_behoudt_eigen_woning_config(self) -> None:
        """Jaarresolutie mag eigen-woning-configuratie niet weggooien."""
        config, _ = laad_tarieven(2026)

        resolved, _ = resolve_tariefwaarden_voor_jaar(config, 2026, [])

        assert resolved.eigen_woning is not None
        assert resolved.eigen_woning.tariefsaanpassing_pct == config.eigen_woning.tariefsaanpassing_pct
        assert resolved.eigen_woning.wet_hillen_pct == config.eigen_woning.wet_hillen_pct

    def test_resolve_tariefwaarden_behoudt_ahk_aow_factor(self) -> None:
        """Jaarresolutie moet de AOW-factor van AHK behouden."""
        config, _ = laad_tarieven(2025)

        resolved, _ = resolve_tariefwaarden_voor_jaar(config, 2025, [])

        assert resolved.ahk_aow_factor == config.ahk_aow_factor


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
        assert config.jaar == 2026

    def test_fallback_gebruikt_laatstbekende_jaar(self, tmp_path: Path, monkeypatch) -> None:
        """Bij een gat in jaren wordt het laatst bekende jaar <= doeljaar gebruikt."""
        bron_2025 = Path(__file__).resolve().parents[1] / "config" / "belasting_2025.json"
        bron_2026 = Path(__file__).resolve().parents[1] / "config" / "belasting_2026.json"

        (tmp_path / "belasting_2025.json").write_text(
            bron_2025.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        data_2027 = json.loads(bron_2026.read_text(encoding="utf-8"))
        data_2027["jaar"] = 2027
        (tmp_path / "belasting_2027.json").write_text(
            json.dumps(data_2027, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        monkeypatch.setattr(belasting_loader, "_CONFIG_DIR", tmp_path)

        config, melding = laad_tarieven(2026)

        assert config.jaar == 2025
        assert "2025" in melding
        assert "laatst bekend" in melding

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


class TestHeffingskortingen:
    """Tests voor AHK en AOW-correctie."""

    def test_ahk_aow_heel_jaar_gebruikt_factor_op_maximum(self) -> None:
        """AOW-factor wordt op AHK-maximum toegepast voor afbouw."""
        config, _ = laad_tarieven(2025)
        inkomen = Decimal("39200")

        ahk_config = config.ahk
        afbouw = max(Decimal("0"), inkomen - ahk_config.afbouw_inkomen_van) * ahk_config.afbouw_pct
        verwacht = max(ahk_config.minimum, (ahk_config.max_bedrag * config.ahk_aow_factor) - afbouw)

        berekend = bereken_ahk_met_aow(inkomen, config, Decimal("1"))
        assert float(berekend) == pytest.approx(float(verwacht), rel=1e-9)

    def test_ahk_aow_deeljaar_gebruikt_gewogen_maximum(self) -> None:
        """Deeljaar AOW gebruikt een gewogen maximum, daarna afbouw."""
        config, _ = laad_tarieven(2025)
        inkomen = Decimal("39200")
        aow_breuk = Decimal("0.5")

        ahk_config = config.ahk
        gewogen_factor = (Decimal("1") - aow_breuk) + (aow_breuk * config.ahk_aow_factor)
        afbouw = max(Decimal("0"), inkomen - ahk_config.afbouw_inkomen_van) * ahk_config.afbouw_pct
        verwacht = max(ahk_config.minimum, (ahk_config.max_bedrag * gewogen_factor) - afbouw)

        berekend = bereken_ahk_met_aow(inkomen, config, aow_breuk)
        assert float(berekend) == pytest.approx(float(verwacht), rel=1e-9)


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

    def test_box3_verschillende_spaargeld_fracties(self) -> None:
        """Box3 heffing verschilt op basis van spaargeld_fractie."""
        vermogen = Decimal("200000")
        config, _ = laad_tarieven(2026)
        
        # 100% spaargeld (laagste forfaitair rendement)
        heffing_sparen, _ = bereken_box3_heffing(
            vermogen, config, heeft_partner=False, spaargeld_fractie=Decimal("1.0")
        )
        
        # 100% beleggingen (hoogste forfaitair rendement)
        heffing_beleggen, _ = bereken_box3_heffing(
            vermogen, config, heeft_partner=False, spaargeld_fractie=Decimal("0.0")
        )
        
        # 50/50
        heffing_mix, _ = bereken_box3_heffing(
            vermogen, config, heeft_partner=False, spaargeld_fractie=Decimal("0.5")
        )
        
        # Beleggen heeft hoger fictief rendement → hogere heffing
        assert heffing_sparen < heffing_mix < heffing_beleggen


class TestBelastingConfigOpslag:
    """Tests voor directe opslag van belastingconfiguraties."""

    def test_schrijf_belastingconfig_json_maakt_backup_bij_overschrijven(self, tmp_path: Path) -> None:
        data_eerste = {
            "jaar": 2030,
            "box1_niet_aow": {"schijven": [{"tot": 10000, "tarief": 0.1}]},
            "box1_aow": {"schijven": [{"tot": 10000, "tarief": 0.1}]},
            "algemene_heffingskorting": {"max": 1, "afbouw_inkomen_van": 1, "afbouw_pct": 0.1, "minimum": 0},
            "arbeidskorting": {"max": 1, "afbouw_drempel": 1, "afbouw_pct": 0.1, "minimum": 0},
            "ouderenkorting": {"max": 1, "afbouw_inkomen_van": 1, "afbouw_pct": 0.1, "minimum": 0},
            "box3": {"vrijstelling_per_persoon": 1, "tarief": 0.36, "forfaitair_spaargeld": 0.01, "forfaitair_overig": 0.05, "_disclaimer": "test"},
            "aow_bedrag": {"alleenstaande_per_maand": 1, "gehuwd_of_samenwonend_per_maand": 1},
        }
        data_tweede = dict(data_eerste)
        data_tweede["box3"] = dict(data_eerste["box3"])
        data_tweede["box3"]["forfaitair_spaargeld"] = 0.02

        eerste_pad, eerste_backup = schrijf_belastingconfig_json(2030, data_eerste, config_dir=tmp_path)
        tweede_pad, tweede_backup = schrijf_belastingconfig_json(2030, data_tweede, config_dir=tmp_path)

        assert eerste_pad == tweede_pad
        assert eerste_backup is None
        assert tweede_backup is not None
        assert tweede_backup.exists()
        backup_data = json.loads(tweede_backup.read_text(encoding="utf-8"))
        assert backup_data["box3"]["forfaitair_spaargeld"] == 0.01

    def test_schrijf_belastingconfig_json_is_direct_herlaadbaar(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        bron_pad = Path(__file__).resolve().parents[1] / "config" / "belasting_2026.json"
        data = json.loads(bron_pad.read_text(encoding="utf-8"))
        data["jaar"] = 2031
        data["box3"]["forfaitair_spaargeld"] = 0.01234
        data["box3"]["forfaitair_overig"] = 0.06789

        schrijf_belastingconfig_json(2031, data, config_dir=tmp_path)
        monkeypatch.setattr("pensioen.tax.belasting_loader._CONFIG_DIR", tmp_path)

        config, melding = laad_tarieven(2031)

        assert melding == ""
        assert config.jaar == 2031
        assert config.box3.forfaitair_spaargeld == Decimal("0.01234")
        assert config.box3.forfaitair_overig == Decimal("0.06789")
