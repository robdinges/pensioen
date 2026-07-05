"""Referentietabellen voor API-codes en labels."""

from __future__ import annotations

from typing import Any

# Canonieke code -> NL label
CATEGORIE_LABELS = {
    "arbeidsinkomen": "Arbeidsinkomen",
    "pensioen_inkomen": "Pensioeninkomen",
    "overig_inkomen": "Overig inkomen",
    "uitgave": "Uitgave",
    "inhouding": "Inhouding",
}

FREQUENTIE_LABELS = {
    "eenmalig": "Eenmalig",
    "maandelijks": "Maandelijks",
    "kwartaal": "Per kwartaal",
    "halfjaarlijks": "Per halfjaar",
    "jaarlijks": "Jaarlijks",
}

BEDRAG_TYPE_LABELS = {
    "bruto": "Bruto",
    "netto": "Netto",
}

BELEGGINGS_TYPE_LABELS = {
    "sparen": "Sparen",
    "beleggen": "Beleggen",
}

VERMOGENS_TYPE_LABELS = {
    "spaargeld": "Spaargeld",
    "beleggingen": "Beleggingen",
    "eigen_woning": "Eigen woning",
    "hypotheek": "Hypotheek",
    "auto": "Auto",
    "kunst": "Kunst",
    "boot": "Boot",
    "overig": "Overig",
}

FOUTCODE_LABELS = {
    "derived_scenario_requires_list": "Afgeleid scenario vereist ook een scenario_lijst met het parent scenario.",
    "inheritance_validation_error": "De scenario-relaties bevatten een fout (bijv. cirkel of ontbrekende parent).",
    "berekening_input_error": "De invoer voor de berekening is ongeldig.",
}

INPUT_HINTS = {
    "berekening": {
        "required": ["scenario", "persoon1", "jaar_van", "jaar_tot"],
        "defaults": {
            "persoon2": None,
            "records1": [],
            "records2": [],
            "scenario_lijst": [],
        },
    },
    "scenario": {
        "required": ["naam"],
        "defaults": {
            "inflatie_pct": "2",
            "box3_meenemen": True,
            "componenten": [],
            "incidentele_items": [],
            "vermogensitems": [],
        },
    },
    "persoon": {
        "required": ["naam", "geboortedatum"],
        "defaults": {
            "heeft_partner": False,
            "partner_id": None,
        },
    },
    "component": {
        "required": ["omschrijving", "categorie", "persoon", "bedrag"],
        "defaults": {
            "bedrag_type": "bruto",
            "frequentie": "maandelijks",
            "beleggings_type": "sparen",
            "groei_pct": "0",
        },
    },
}

# Synoniem -> canonieke code
CATEGORIE_CODES = {
    "arbeidsinkomen": "arbeidsinkomen",
    "arbeids_inkomen": "arbeidsinkomen",
    "pensioeninkomen": "pensioen_inkomen",
    "pensioen_inkomen": "pensioen_inkomen",
    "overiginkomen": "overig_inkomen",
    "overig_inkomen": "overig_inkomen",
    "uitgave": "uitgave",
    "inhouding": "inhouding",
}

FREQUENTIE_CODES = {
    "eenmalig": "eenmalig",
    "maandelijks": "maandelijks",
    "kwartaal": "kwartaal",
    "halfjaarlijks": "halfjaarlijks",
    "half_jaarlijks": "halfjaarlijks",
    "jaarlijks": "jaarlijks",
}

BEDRAG_TYPE_CODES = {
    "bruto": "bruto",
    "netto": "netto",
}

BELEGGINGS_TYPE_CODES = {
    "sparen": "sparen",
    "spaar": "sparen",
    "beleggen": "beleggen",
}

VERMOGENS_TYPE_CODES = {
    "spaargeld": "spaargeld",
    "beleggingen": "beleggingen",
    "eigen_woning": "eigen_woning",
    "eigenwoning": "eigen_woning",
    "hypotheek": "hypotheek",
    "auto": "auto",
    "kunst": "kunst",
    "boot": "boot",
    "overig": "overig",
}


def normaliseer_code_waarde(waarde: str) -> str:
    """Normaliseer tekst naar code-sleutel."""
    return waarde.strip().lower().replace("-", "_").replace(" ", "_")


def map_code(waarde: Any, mapping: dict[str, str]) -> Any:
    """Map een mogelijk synoniem naar canonieke code."""
    if not isinstance(waarde, str):
        return waarde
    sleutel = normaliseer_code_waarde(waarde)
    return mapping.get(sleutel, waarde)


def codes_en_labels() -> dict[str, dict[str, str]]:
    """Geef de publieksset van canonieke codes en labels."""
    return {
        "categorieen": CATEGORIE_LABELS,
        "frequenties": FREQUENTIE_LABELS,
        "bedrag_types": BEDRAG_TYPE_LABELS,
        "beleggings_types": BELEGGINGS_TYPE_LABELS,
        "vermogens_types": VERMOGENS_TYPE_LABELS,
        "foutcodes": FOUTCODE_LABELS,
    }


def input_hints() -> dict[str, dict[str, object]]:
    """Geef input hints voor UI-form generatie."""
    return INPUT_HINTS
