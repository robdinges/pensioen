"""Contract- en integratietests voor centrale Epic 4-detailoutput."""

from __future__ import annotations

import io
from decimal import Decimal

import openpyxl

from pensioen.calculations.cashflow_engine import bereken_huishouden
from pensioen.calculations.detail_output_engine import (
    AFGELEIDE_DETAILVELDEN,
    PRIMAIRE_DETAILVELDEN,
    ontbrekende_detailvelden,
)
from pensioen.reports.rapport_engine import genereer_rapport
from pensioen.tax.belasting_loader import laad_tarieven_bereik


def test_accountantdetail_voldoet_aan_bron_en_afgeleid_contract(
    persoon1,
    persoon2,
    scenario_standaard,
) -> None:
    cashflow = bereken_huishouden(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2026,
        belasting_configs=laad_tarieven_bereik(2026, 2026),
    )

    detail = cashflow.jaren[0].accountant_detail
    assert not ontbrekende_detailvelden(detail)
    assert PRIMAIRE_DETAILVELDEN.isdisjoint(AFGELEIDE_DETAILVELDEN)


def test_accountantdetail_volgt_meerjarige_vermogensreeks(
    persoon1,
    scenario_standaard,
) -> None:
    cashflow = bereken_huishouden(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2027,
        belasting_configs=laad_tarieven_bereik(2026, 2027),
    )

    detail_2026 = cashflow.jaren[0].accountant_detail
    detail_2027 = cashflow.jaren[1].accountant_detail
    assert detail_2027["saldo_begin_jaar"] == detail_2026["saldo_einde_jaar"]


def test_excel_accountantdetail_consumeert_engine_output(
    persoon1,
    scenario_standaard,
) -> None:
    cashflow = bereken_huishouden(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=None,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2026,
        belasting_configs=laad_tarieven_bereik(2026, 2026),
    )

    werkboek = openpyxl.load_workbook(io.BytesIO(genereer_rapport(cashflow)))
    werkblad = werkboek["Accountantdetail"]
    detail = cashflow.jaren[0].accountant_detail

    assert werkblad["A2"].value == 2026
    assert Decimal(str(werkblad["B2"].value)) == detail["bruto_p1"]
    assert Decimal(str(werkblad["I2"].value)) == detail["box3_heffing"]


def test_jaarresultaat_en_accountantdetail_blijven_rekenkundig_consistent(
    persoon1,
    persoon2,
    scenario_standaard,
) -> None:
    """Samenvatting, maandregels en detailoutput volgen dezelfde engine-uitkomst."""
    cashflow = bereken_huishouden(
        scenario=scenario_standaard,
        persoon1=persoon1,
        persoon2=persoon2,
        records1=[],
        records2=[],
        jaar_van=2026,
        jaar_tot=2026,
        belasting_configs=laad_tarieven_bereik(2026, 2026),
    )

    jaar = cashflow.jaren[0]
    detail = jaar.accountant_detail
    belasting_uit_maanden = sum(
        (
            maand.belasting_p1
            + maand.belasting_p2
            + maand.box3_heffing
        )
        for maand in jaar.maanden
    )
    netto_belasting_uit_detail = (
        detail["netto_bel_p1"]
        + detail["netto_bel_p2"]
        + detail["box3_heffing"]
    )
    netto_belasting_uit_maanden = sum(
        (
            maand.belasting_p1
            + maand.belasting_p2
            + maand.box3_heffing
            - maand.heffingskorting_p1
            - maand.heffingskorting_p2
        )
        for maand in jaar.maanden
    )

    assert Decimal(str(jaar.jaar_samenvatting["belasting"])) == belasting_uit_maanden
    assert abs(netto_belasting_uit_detail - netto_belasting_uit_maanden) <= Decimal("0.12")
