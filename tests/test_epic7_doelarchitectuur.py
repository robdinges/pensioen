"""Architectuurpoorten voor Epic 7."""

from __future__ import annotations

from pathlib import Path

from pensioen.models.output_contract import (
    OUTPUT_CONTRACT,
    OUTPUT_CONTRACT_VERSION,
    AccountantDetailDTO,
    JaarSamenvattingDTO,
)


def test_resultaatcontract_is_centraal_en_versieerbaar() -> None:
    assert OUTPUT_CONTRACT["versie"] == OUTPUT_CONTRACT_VERSION == "1.0"
    assert JaarSamenvattingDTO.__required_keys__ >= {
        "jaar",
        "bruto",
        "belasting",
        "netto_inkomen",
        "netto_cashflow",
        "vermogen_einde_jaar",
    }
    assert "totaal_netto_inkomen" in AccountantDetailDTO.__optional_keys__


def test_presentatie_en_scenariovergelijking_omzeilen_resultaatservice_niet() -> None:
    projectroot = Path(__file__).parents[1]
    gecontroleerde_bestanden = [
        projectroot / "src/pensioen/api/main.py",
        projectroot / "src/pensioen/calculations/scenario_engine.py",
    ]
    for bestand in gecontroleerde_bestanden:
        inhoud = bestand.read_text(encoding="utf-8")
        assert "bereken_huishouden" not in inhoud, bestand
