"""Directe unit-tests voor Epic 1 fiscale bouwstenen."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_HALF_UP, Decimal

from pensioen.tax.belasting_engine import bereken_premies_volksverzekeringen
from pensioen.tax.belasting_loader import PremiesConfig, laad_tarieven
from pensioen.tax.heffingskorting import (
    bereken_ahk,
    bereken_ahk_met_aow,
    bereken_alleenstaandeouderenkorting,
    bereken_arbeidskorting,
    bereken_ouderenkorting,
    bereken_totale_heffingskortingen,
)

CENT = Decimal("0.01")


def _rond_cent(bedrag: Decimal) -> Decimal:
    return bedrag.quantize(CENT, rounding=ROUND_HALF_UP)


class TestPremiesVolksverzekeringen:
    def test_geen_premiesconfig_geeft_nulcomponenten(self) -> None:
        config, _ = laad_tarieven(2025)
        config_zonder_premies = replace(config, premies=None)

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=Decimal("50000"),
            config=config_zonder_premies,
            is_aow=False,
        )

        assert premie_aow == Decimal("0")
        assert premie_anw == Decimal("0")
        assert premie_wlz == Decimal("0")
        assert totaal == Decimal("0")

    def test_inkomen_onder_premiegrens_gebruikt_volledig_inkomen(self) -> None:
        config, _ = laad_tarieven(2025)
        assert config.premies is not None
        inkomen = Decimal("10000")

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=False,
        )

        verwacht_aow = _rond_cent(inkomen * config.premies.aow_tarief_niet_aow)
        verwacht_anw = _rond_cent(inkomen * config.premies.anw_tarief)
        verwacht_wlz = _rond_cent(inkomen * config.premies.wlz_tarief)

        assert premie_aow == verwacht_aow
        assert premie_anw == verwacht_anw
        assert premie_wlz == verwacht_wlz
        assert totaal == verwacht_aow + verwacht_anw + verwacht_wlz

    def test_inkomen_exact_op_premiegrens(self) -> None:
        config, _ = laad_tarieven(2026)
        assert config.premies is not None
        inkomen = config.premies.premiegrens

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=False,
        )

        assert premie_aow == _rond_cent(inkomen * config.premies.aow_tarief_niet_aow)
        assert premie_anw == _rond_cent(inkomen * config.premies.anw_tarief)
        assert premie_wlz == _rond_cent(inkomen * config.premies.wlz_tarief)
        assert totaal == premie_aow + premie_anw + premie_wlz

    def test_inkomen_boven_premiegrens_gebruikt_max_grondslag(self) -> None:
        config, _ = laad_tarieven(2026)
        assert config.premies is not None
        inkomen = config.premies.premiegrens + Decimal("25000")
        grondslag = config.premies.premiegrens

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=False,
        )

        assert premie_aow == _rond_cent(grondslag * config.premies.aow_tarief_niet_aow)
        assert premie_anw == _rond_cent(grondslag * config.premies.anw_tarief)
        assert premie_wlz == _rond_cent(grondslag * config.premies.wlz_tarief)
        assert totaal == premie_aow + premie_anw + premie_wlz

    def test_aow_status_beinvloedt_alleen_aow_premie(self) -> None:
        config, _ = laad_tarieven(2025)
        assert config.premies is not None
        inkomen = Decimal("30000")

        premie_aow_niet, premie_anw_niet, premie_wlz_niet, totaal_niet = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=False,
        )
        premie_aow_wel, premie_anw_wel, premie_wlz_wel, totaal_wel = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=True,
        )

        assert premie_aow_niet > Decimal("0")
        assert premie_aow_wel == Decimal("0")
        assert premie_anw_wel == premie_anw_niet
        assert premie_wlz_wel == premie_wlz_niet
        assert totaal_niet - totaal_wel == premie_aow_niet

    def test_anw_en_wlz_blijven_actief_bij_volledig_aow(self) -> None:
        config, _ = laad_tarieven(2026)
        inkomen = Decimal("38883")

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=inkomen,
            config=config,
            is_aow=True,
        )

        assert premie_aow == Decimal("0")
        assert premie_anw > Decimal("0")
        assert premie_wlz > Decimal("0")
        assert totaal == premie_anw + premie_wlz

    def test_premiecomponenten_ronden_af_op_centen(self) -> None:
        config, _ = laad_tarieven(2026)
        config_afronding = replace(
            config,
            premies=PremiesConfig(
                premiegrens=Decimal("100"),
                aow_tarief_niet_aow=Decimal("0.01005"),
                aow_tarief_aow=Decimal("0"),
                anw_tarief=Decimal("0.02005"),
                wlz_tarief=Decimal("0.03005"),
            ),
        )

        premie_aow, premie_anw, premie_wlz, totaal = bereken_premies_volksverzekeringen(
            bruto_inkomen=Decimal("100"),
            config=config_afronding,
            is_aow=False,
        )

        assert premie_aow == Decimal("1.01")
        assert premie_anw == Decimal("2.01")
        assert premie_wlz == Decimal("3.01")
        assert totaal == Decimal("6.03")


class TestLosseHeffingskortingen:
    def test_bereken_ahk_onder_afbouwgrens(self) -> None:
        config, _ = laad_tarieven(2025)
        inkomen = config.ahk.afbouw_inkomen_van - Decimal("1")

        assert bereken_ahk(inkomen, config) == config.ahk.max_bedrag

    def test_bereken_ahk_exact_op_afbouwgrens(self) -> None:
        config, _ = laad_tarieven(2025)

        assert bereken_ahk(config.ahk.afbouw_inkomen_van, config) == config.ahk.max_bedrag

    def test_bereken_ahk_boven_afbouwgrens(self) -> None:
        config, _ = laad_tarieven(2025)
        inkomen = config.ahk.afbouw_inkomen_van + Decimal("1000")
        verwacht = Decimal('3005')  # 3004,63 wordt bij de aanslag naar boven afgerond.

        assert bereken_ahk(inkomen, config) == verwacht

    def test_bereken_ahk_komt_op_minimumvloer(self) -> None:
        config, _ = laad_tarieven(2025)
        inkomen = Decimal("1000000")

        assert bereken_ahk(inkomen, config) == config.ahk.minimum

    def test_bereken_arbeidskorting_geen_arbeidsinkomen(self) -> None:
        config, _ = laad_tarieven(2026)

        assert bereken_arbeidskorting(Decimal("0"), config) == Decimal("0")

    def test_bereken_arbeidskorting_laag_arbeidsinkomen(self) -> None:
        config, _ = laad_tarieven(2026)
        inkomen = Decimal("1000")

        assert bereken_arbeidskorting(inkomen, config) == inkomen

    def test_bereken_arbeidskorting_rond_maximumlogica(self) -> None:
        config, _ = laad_tarieven(2026)
        net_onder_max = config.arbeidskorting.max_bedrag - Decimal("1")
        net_boven_max = config.arbeidskorting.max_bedrag + Decimal("1")

        korting_onder = bereken_arbeidskorting(net_onder_max, config)
        korting_boven = bereken_arbeidskorting(net_boven_max, config)

        assert korting_onder == net_onder_max
        assert korting_boven == config.arbeidskorting.max_bedrag

    def test_bereken_arbeidskorting_boven_afbouwdrempel(self) -> None:
        config, _ = laad_tarieven(2026)
        inkomen = config.arbeidskorting.afbouw_drempel + Decimal("1000")
        verwacht = config.arbeidskorting.max_bedrag - (Decimal("1000") * config.arbeidskorting.afbouw_pct)

        assert bereken_arbeidskorting(inkomen, config) == verwacht

    def test_bereken_arbeidskorting_houdt_minimumvloer_aan(self) -> None:
        config, _ = laad_tarieven(2026)
        inkomen = Decimal("1000000")

        assert bereken_arbeidskorting(inkomen, config) == config.arbeidskorting.minimum

    def test_bereken_ouderenkorting_zonder_aow(self) -> None:
        config, _ = laad_tarieven(2025)

        assert bereken_ouderenkorting(Decimal("30000"), config, is_aow=False) == Decimal("0")

    def test_bereken_ouderenkorting_met_aow_onder_afbouwgrens(self) -> None:
        config, _ = laad_tarieven(2025)
        inkomen = config.ouderenkorting.afbouw_inkomen_van - Decimal("1")

        assert bereken_ouderenkorting(inkomen, config, is_aow=True) == config.ouderenkorting.max_bedrag

    def test_bereken_ouderenkorting_met_aow_boven_afbouwgrens(self) -> None:
        config, _ = laad_tarieven(2025)
        inkomen = config.ouderenkorting.afbouw_inkomen_van + Decimal("1000")
        verwacht = config.ouderenkorting.max_bedrag - (Decimal("1000") * config.ouderenkorting.afbouw_pct)

        assert bereken_ouderenkorting(inkomen, config, is_aow=True) == verwacht

    def test_bereken_ouderenkorting_met_aow_houdt_minimumvloer_aan(self) -> None:
        config, _ = laad_tarieven(2025)

        assert bereken_ouderenkorting(Decimal("1000000"), config, is_aow=True) == config.ouderenkorting.minimum

    def test_bereken_alleenstaandeouderenkorting_zonder_aow(self) -> None:
        config, _ = laad_tarieven(2025)

        assert (
            bereken_alleenstaandeouderenkorting(
                Decimal("20000"), config, is_aow=False, is_alleenstaand=True
            )
            == Decimal("0")
        )

    def test_bereken_alleenstaandeouderenkorting_niet_alleenstaand(self) -> None:
        config, _ = laad_tarieven(2025)

        assert (
            bereken_alleenstaandeouderenkorting(
                Decimal("20000"), config, is_aow=True, is_alleenstaand=False
            )
            == Decimal("0")
        )

    def test_bereken_alleenstaandeouderenkorting_geen_config(self) -> None:
        config, _ = laad_tarieven(2025)
        zonder_aok = replace(config, alleenstaandeouderenkorting=None)

        assert (
            bereken_alleenstaandeouderenkorting(
                Decimal("20000"), zonder_aok, is_aow=True, is_alleenstaand=True
            )
            == Decimal("0")
        )

    def test_bereken_alleenstaandeouderenkorting_geldig_aow_en_alleenstaand(self) -> None:
        config, _ = laad_tarieven(2025)

        assert (
            bereken_alleenstaandeouderenkorting(
                Decimal("20000"), config, is_aow=True, is_alleenstaand=True
            )
            == config.alleenstaandeouderenkorting.max_bedrag
        )

    def test_bereken_alleenstaandeouderenkorting_jaarafhankelijk_afbouwgedrag(self) -> None:
        config_2025, _ = laad_tarieven(2025)
        config_2026, _ = laad_tarieven(2026)
        hoog_inkomen = Decimal("86813")

        aok_2025 = bereken_alleenstaandeouderenkorting(
            hoog_inkomen, config_2025, is_aow=True, is_alleenstaand=True
        )
        aok_2026 = bereken_alleenstaandeouderenkorting(
            hoog_inkomen, config_2026, is_aow=True, is_alleenstaand=True
        )

        assert aok_2025 == config_2025.alleenstaandeouderenkorting.max_bedrag
        assert aok_2026 == config_2026.alleenstaandeouderenkorting.minimum


class TestTotaleHeffingskortingen:
    def test_totaal_geen_arbeid_geen_aow(self) -> None:
        config, _ = laad_tarieven(2025)
        bruto = Decimal("30000")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=Decimal("0"),
            config=config,
            is_aow=False,
            aow_breuk=Decimal("0"),
            is_alleenstaand=True,
        )

        verwacht = _rond_cent(bereken_ahk_met_aow(bruto, config, Decimal("0")))
        assert totaal == verwacht

    def test_totaal_met_arbeid_zonder_aow(self) -> None:
        config, _ = laad_tarieven(2026)
        bruto = Decimal("50000")
        arbeid = Decimal("50000")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=arbeid,
            config=config,
            is_aow=False,
            aow_breuk=Decimal("0"),
            is_alleenstaand=True,
        )

        verwacht = (
            _rond_cent(bereken_ahk_met_aow(bruto, config, Decimal("0")))
            + _rond_cent(bereken_arbeidskorting(arbeid, config))
        )
        assert totaal == verwacht

    def test_totaal_met_aow_zonder_arbeid(self) -> None:
        config, _ = laad_tarieven(2025)
        bruto = Decimal("30000")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=Decimal("0"),
            config=config,
            is_aow=True,
            aow_breuk=Decimal("1"),
            is_alleenstaand=False,
        )

        verwacht = (
            _rond_cent(bereken_ahk_met_aow(bruto, config, Decimal("1")))
            + _rond_cent(bereken_ouderenkorting(bruto, config, is_aow=True))
        )
        assert totaal == verwacht

    def test_totaal_alleenstaand_aow_met_aok(self) -> None:
        config, _ = laad_tarieven(2025)
        bruto = Decimal("86813")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=Decimal("0"),
            config=config,
            is_aow=True,
            aow_breuk=Decimal("1"),
            is_alleenstaand=True,
        )

        verwacht = (
            _rond_cent(bereken_ahk_met_aow(bruto, config, Decimal("1")))
            + _rond_cent(bereken_ouderenkorting(bruto, config, is_aow=True))
            + _rond_cent(
                bereken_alleenstaandeouderenkorting(
                    bruto, config, is_aow=True, is_alleenstaand=True
                )
            )
        )
        assert totaal == verwacht

    def test_totaal_met_deeljaar_aow_breuk(self) -> None:
        config, _ = laad_tarieven(2025)
        bruto = Decimal("39200")
        arbeid = Decimal("0")
        aow_breuk = Decimal("0.5")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=arbeid,
            config=config,
            is_aow=True,
            aow_breuk=aow_breuk,
            is_alleenstaand=True,
        )

        verwacht = (
            _rond_cent(bereken_ahk_met_aow(bruto, config, aow_breuk))
            + _rond_cent(bereken_arbeidskorting(arbeid, config))
            + _rond_cent(bereken_ouderenkorting(bruto, config, is_aow=True))
            + _rond_cent(
                bereken_alleenstaandeouderenkorting(
                    bruto,
                    config,
                    is_aow=True,
                    is_alleenstaand=True,
                )
            )
        )
        assert totaal == verwacht

    def test_totaal_is_exact_som_van_losse_componenten(self) -> None:
        config, _ = laad_tarieven(2026)
        bruto = Decimal("60123.45")
        arbeid = Decimal("42321.10")
        aow_breuk = Decimal("0.3")

        totaal = bereken_totale_heffingskortingen(
            bruto_inkomen=bruto,
            arbeidsinkomen=arbeid,
            config=config,
            is_aow=True,
            aow_breuk=aow_breuk,
            is_alleenstaand=True,
        )

        som_componenten = (
            _rond_cent(bereken_ahk_met_aow(bruto, config, aow_breuk))
            + _rond_cent(bereken_arbeidskorting(arbeid, config))
            + _rond_cent(bereken_ouderenkorting(bruto, config, is_aow=True))
            + _rond_cent(
                bereken_alleenstaandeouderenkorting(
                    bruto,
                    config,
                    is_aow=True,
                    is_alleenstaand=True,
                )
            )
        )

        assert totaal == som_componenten
