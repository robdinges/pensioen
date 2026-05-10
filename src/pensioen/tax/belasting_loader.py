"""Laadfunctie voor jaarlĳkse belastingconfiguratie vanuit JSON-bestanden."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuratiemap: instelbaar via omgevingsvariabele voor testbaarheid
_CONFIG_DIR = Path(
    os.environ.get(
        "PENSIOEN_CONFIG_DIR",
        str(Path(__file__).parents[3] / "config"),
    )
)


@dataclass
class SchijfConfig:
    """Eén belastingschijf."""

    tot: Decimal | None  # None = geen bovengrens (laatste schijf)
    tarief: Decimal


@dataclass
class HeffingskortingConfig:
    """Parameters voor een heffingskorting met afbouw."""

    max_bedrag: Decimal
    afbouw_inkomen_van: Decimal
    afbouw_pct: Decimal
    minimum: Decimal = Decimal("0")


@dataclass
class ArbeidskortingConfig:
    """Parameters voor de arbeidskorting."""

    max_bedrag: Decimal
    afbouw_drempel: Decimal
    afbouw_pct: Decimal
    minimum: Decimal = Decimal("0")


@dataclass
class Box3Config:
    """Parameters voor box 3 vermogensrendementsheffing."""

    vrijstelling_per_persoon: Decimal
    tarief: Decimal  # belastingpercentage over het fictief rendement (bijv. 0.36)
    forfaitair_spaargeld: Decimal  # fictief rendement spaargeld (bijv. 0.015)
    forfaitair_overig: Decimal    # fictief rendement beleggingen/overig (bijv. 0.06)
    disclaimer: str


@dataclass
class AOWBedragConfig:
    """Bruto AOW-bedragen per maand."""

    alleenstaande_per_maand: Decimal
    gehuwd_of_samenwonend_per_maand: Decimal


@dataclass
class BelastingConfig:
    """Volledige belastingconfiguratie voor één belastingjaar."""

    jaar: int
    box1_niet_aow: list[SchijfConfig]
    box1_aow: list[SchijfConfig]
    ahk: HeffingskortingConfig
    arbeidskorting: ArbeidskortingConfig
    ouderenkorting: HeffingskortingConfig
    box3: Box3Config
    aow_bedrag: AOWBedragConfig


def _d(waarde: float | int | str) -> Decimal:
    """Zet een numerieke waarde om naar Decimal via string (voorkomt float-fouten)."""
    return Decimal(str(waarde))


def _laad_schijven(schijven_data: list[dict]) -> list[SchijfConfig]:
    return [
        SchijfConfig(
            tot=_d(s["tot"]) if s["tot"] is not None else None,
            tarief=_d(s["tarief"]),
        )
        for s in schijven_data
    ]


def laad_tarieven(jaar: int) -> tuple[BelastingConfig, str]:
    """
    Laad de belastingconfiguratie voor het opgegeven jaar.

    Als het bestand voor het gevraagde jaar niet bestaat, wordt het meest recente
    beschikbare jaar gebruikt als aanname.

    Returns:
        Een tuple van (BelastingConfig, aanname_melding).
        aanname_melding is leeg als het exacte jaar beschikbaar is.
    """
    config_pad = _CONFIG_DIR / f"belasting_{jaar}.json"
    aanname_melding = ""

    if not config_pad.exists():
        # Zoek het meest recente beschikbare belastingbestand
        beschikbaar = sorted(
            _CONFIG_DIR.glob("belasting_*.json"),
            key=lambda p: int(p.stem.split("_")[1]),
            reverse=True,
        )
        if not beschikbaar:
            raise FileNotFoundError(
                f"Geen belastingconfiguratiebestanden gevonden in {_CONFIG_DIR}."
            )
        fallback_pad = beschikbaar[0]
        fallback_jaar = int(fallback_pad.stem.split("_")[1])
        aanname_melding = (
            f"⚠️ Officiële belastingtarieven voor {jaar} zijn nog niet beschikbaar. "
            f"Tarieven van {fallback_jaar} worden als aanname gebruikt. "
            f"Controleer en pas aan via Instellingen > Belastingparameters."
        )
        logger.warning(aanname_melding)
        config_pad = fallback_pad

    with config_pad.open(encoding="utf-8") as f:
        data = json.load(f)

    config = BelastingConfig(
        jaar=data["jaar"],
        box1_niet_aow=_laad_schijven(data["box1_niet_aow"]["schijven"]),
        box1_aow=_laad_schijven(data["box1_aow"]["schijven"]),
        ahk=HeffingskortingConfig(
            max_bedrag=_d(data["algemene_heffingskorting"]["max"]),
            afbouw_inkomen_van=_d(data["algemene_heffingskorting"]["afbouw_inkomen_van"]),
            afbouw_pct=_d(data["algemene_heffingskorting"]["afbouw_pct"]),
            minimum=_d(data["algemene_heffingskorting"].get("minimum", 0)),
        ),
        arbeidskorting=ArbeidskortingConfig(
            max_bedrag=_d(data["arbeidskorting"]["max"]),
            afbouw_drempel=_d(data["arbeidskorting"]["afbouw_drempel"]),
            afbouw_pct=_d(data["arbeidskorting"]["afbouw_pct"]),
            minimum=_d(data["arbeidskorting"].get("minimum", 0)),
        ),
        ouderenkorting=HeffingskortingConfig(
            max_bedrag=_d(data["ouderenkorting"]["max"]),
            afbouw_inkomen_van=_d(data["ouderenkorting"]["afbouw_inkomen_van"]),
            afbouw_pct=_d(data["ouderenkorting"]["afbouw_pct"]),
            minimum=_d(data["ouderenkorting"].get("minimum", 0)),
        ),
        box3=Box3Config(
            vrijstelling_per_persoon=_d(data["box3"]["vrijstelling_per_persoon"]),
            tarief=_d(data["box3"]["tarief"]),
            forfaitair_spaargeld=_d(data["box3"]["forfaitair_spaargeld"]),
            forfaitair_overig=_d(data["box3"]["forfaitair_overig"]),
            disclaimer=data["box3"]["_disclaimer"],
        ),
        aow_bedrag=AOWBedragConfig(
            alleenstaande_per_maand=_d(data["aow_bedrag"]["alleenstaande_per_maand"]),
            gehuwd_of_samenwonend_per_maand=_d(
                data["aow_bedrag"]["gehuwd_of_samenwonend_per_maand"]
            ),
        ),
    )
    return config, aanname_melding


def beschikbare_jaren() -> set[int]:
    """Geef de jaren terug waarvoor een eigen belastingconfig-bestand beschikbaar is."""
    return {
        int(p.stem.split("_")[1])
        for p in _CONFIG_DIR.glob("belasting_*.json")
        if p.stem.split("_")[1].isdigit()
    }


def laad_tarieven_bereik(jaar_van: int, jaar_tot: int) -> dict[int, tuple[BelastingConfig, str]]:
    """Laad belastingconfiguraties voor een reeks jaren (jaar_van t/m jaar_tot inclusief)."""
    return {jaar: laad_tarieven(jaar) for jaar in range(jaar_van, jaar_tot + 1)}
