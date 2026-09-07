"""Getypeerde, versieerbare contracten voor publieke resultaatoutput."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, NotRequired, TypedDict


OUTPUT_CONTRACT_VERSION = "1.0"


class JaarSamenvattingDTO(TypedDict):
    """Stabiele jaarsamenvatting voor API- en presentatieconsumenten."""

    jaar: int
    bruto: Decimal
    belasting: Decimal
    netto: Decimal
    netto_inkomen: Decimal
    netto_cashflow: Decimal
    netto_per_maand: Decimal
    netto_inkomen_per_maand: Decimal
    vermogen_einde_jaar: Decimal
    arbeid_p1: NotRequired[Decimal]
    arbeid_p2: NotRequired[Decimal]
    aow_p1: NotRequired[Decimal]
    aow_p2: NotRequired[Decimal]
    pensioen_p1: NotRequired[Decimal]
    pensioen_p2: NotRequired[Decimal]
    overig: NotRequired[Decimal]
    rendement: NotRequired[Decimal]
    inhoudingen: NotRequired[Decimal]
    huishoudelijke_uitgaven: NotRequired[Decimal]
    eenmalig_ontvangst: NotRequired[Decimal]
    eenmalig_uitgave: NotRequired[Decimal]


class AccountantDetailDTO(TypedDict, total=False):
    netto_aansluiting: list[dict[str, Any]]
    """Kerncontract voor accountantoutput; uitbreidingen blijven additief."""

    jaar: int
    config_jaar: int
    bruto_p1: Decimal
    bruto_p2: Decimal
    netto_p1: Decimal
    netto_p2: Decimal
    totaal_netto_inkomen: Decimal
    totaal_netto_belasting_box1: Decimal
    box3_heffing: Decimal
    saldo_begin_jaar: Decimal
    saldo_einde_jaar: Decimal
    jaar_netto_cashflow: Decimal
    maand_data: list[dict]
    vermogen_rijen: list[dict]


class OutputContractDTO(TypedDict):
    """Metadata waarmee clients de resultaatstructuur valideren."""

    versie: str
    jaarresultaten: str
    accountant: str
    maandresultaten: str


OUTPUT_CONTRACT: OutputContractDTO = {
    "versie": OUTPUT_CONTRACT_VERSION,
    "jaarresultaten": "cashflow.jaren[].jaar_samenvatting",
    "accountant": "cashflow.jaren[].accountant_detail",
    "maandresultaten": "cashflow.jaren[].maanden[]",
}
