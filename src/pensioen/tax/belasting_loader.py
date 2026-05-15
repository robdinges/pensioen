"""Laadfunctie voor jaarlĳkse belastingconfiguratie vanuit JSON-bestanden."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

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


@dataclass
class TariefPeriodeRegel:
    """Gebruikersregel voor één tariefsleutel over een jaarperiode."""

    sleutel: str
    waarde: Decimal
    startjaar: int | None = None
    eindjaar: int | None = None
    inflatie_pct: Decimal = Decimal("0")


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


def config_naar_tariefwaarden(config: BelastingConfig) -> dict[str, Decimal]:
    """Flatten belastingconfig naar sleutel->waarde voor periode-resolutie."""
    waarden: dict[str, Decimal] = {}
    for i, s in enumerate(config.box1_niet_aow, start=1):
        if s.tot is not None:
            waarden[f"box1_niet_aow_s{i}_tot"] = s.tot
        waarden[f"box1_niet_aow_s{i}_tarief"] = s.tarief
    for i, s in enumerate(config.box1_aow, start=1):
        if s.tot is not None:
            waarden[f"box1_aow_s{i}_tot"] = s.tot
        waarden[f"box1_aow_s{i}_tarief"] = s.tarief

    waarden["ahk_max"] = config.ahk.max_bedrag
    waarden["ahk_afbouw_van"] = config.ahk.afbouw_inkomen_van
    waarden["ahk_afbouw_pct"] = config.ahk.afbouw_pct
    waarden["ahk_minimum"] = config.ahk.minimum

    waarden["ak_max"] = config.arbeidskorting.max_bedrag
    waarden["ak_afbouw_drempel"] = config.arbeidskorting.afbouw_drempel
    waarden["ak_afbouw_pct"] = config.arbeidskorting.afbouw_pct
    waarden["ak_minimum"] = config.arbeidskorting.minimum

    waarden["ok_max"] = config.ouderenkorting.max_bedrag
    waarden["ok_afbouw_van"] = config.ouderenkorting.afbouw_inkomen_van
    waarden["ok_afbouw_pct"] = config.ouderenkorting.afbouw_pct
    waarden["ok_minimum"] = config.ouderenkorting.minimum

    waarden["box3_vrijstelling"] = config.box3.vrijstelling_per_persoon
    waarden["box3_tarief"] = config.box3.tarief
    waarden["box3_forfait_spaargeld"] = config.box3.forfaitair_spaargeld
    waarden["box3_forfait_overig"] = config.box3.forfaitair_overig

    waarden["aow_alleenstaand_pm"] = config.aow_bedrag.alleenstaande_per_maand
    waarden["aow_gehuwd_pm"] = config.aow_bedrag.gehuwd_of_samenwonend_per_maand
    return waarden


def pas_tariefwaarden_toe_op_config(
    config: BelastingConfig,
    waarden: dict[str, Decimal],
) -> BelastingConfig:
    """Zet flattened tarieven terug naar een volledige BelastingConfig."""
    box1_niet_aow: list[SchijfConfig] = []
    for i, s in enumerate(config.box1_niet_aow, start=1):
        tot = waarden.get(f"box1_niet_aow_s{i}_tot", s.tot)
        box1_niet_aow.append(
            SchijfConfig(
                tot=tot if isinstance(tot, Decimal) else s.tot,
                tarief=waarden.get(f"box1_niet_aow_s{i}_tarief", s.tarief),
            )
        )

    box1_aow: list[SchijfConfig] = []
    for i, s in enumerate(config.box1_aow, start=1):
        tot = waarden.get(f"box1_aow_s{i}_tot", s.tot)
        box1_aow.append(
            SchijfConfig(
                tot=tot if isinstance(tot, Decimal) else s.tot,
                tarief=waarden.get(f"box1_aow_s{i}_tarief", s.tarief),
            )
        )

    return BelastingConfig(
        jaar=config.jaar,
        box1_niet_aow=box1_niet_aow,
        box1_aow=box1_aow,
        ahk=HeffingskortingConfig(
            max_bedrag=waarden.get("ahk_max", config.ahk.max_bedrag),
            afbouw_inkomen_van=waarden.get("ahk_afbouw_van", config.ahk.afbouw_inkomen_van),
            afbouw_pct=waarden.get("ahk_afbouw_pct", config.ahk.afbouw_pct),
            minimum=waarden.get("ahk_minimum", config.ahk.minimum),
        ),
        arbeidskorting=ArbeidskortingConfig(
            max_bedrag=waarden.get("ak_max", config.arbeidskorting.max_bedrag),
            afbouw_drempel=waarden.get("ak_afbouw_drempel", config.arbeidskorting.afbouw_drempel),
            afbouw_pct=waarden.get("ak_afbouw_pct", config.arbeidskorting.afbouw_pct),
            minimum=waarden.get("ak_minimum", config.arbeidskorting.minimum),
        ),
        ouderenkorting=HeffingskortingConfig(
            max_bedrag=waarden.get("ok_max", config.ouderenkorting.max_bedrag),
            afbouw_inkomen_van=waarden.get("ok_afbouw_van", config.ouderenkorting.afbouw_inkomen_van),
            afbouw_pct=waarden.get("ok_afbouw_pct", config.ouderenkorting.afbouw_pct),
            minimum=waarden.get("ok_minimum", config.ouderenkorting.minimum),
        ),
        box3=Box3Config(
            vrijstelling_per_persoon=waarden.get("box3_vrijstelling", config.box3.vrijstelling_per_persoon),
            tarief=waarden.get("box3_tarief", config.box3.tarief),
            forfaitair_spaargeld=waarden.get("box3_forfait_spaargeld", config.box3.forfaitair_spaargeld),
            forfaitair_overig=waarden.get("box3_forfait_overig", config.box3.forfaitair_overig),
            disclaimer=config.box3.disclaimer,
        ),
        aow_bedrag=AOWBedragConfig(
            alleenstaande_per_maand=waarden.get("aow_alleenstaand_pm", config.aow_bedrag.alleenstaande_per_maand),
            gehuwd_of_samenwonend_per_maand=waarden.get("aow_gehuwd_pm", config.aow_bedrag.gehuwd_of_samenwonend_per_maand),
        ),
    )


def _parse_periode_regel(regel: Any) -> TariefPeriodeRegel | None:
    try:
        if isinstance(regel, dict):
            sleutel_raw = regel.get("sleutel")
            waarde_raw = regel.get("waarde")
            start_raw = regel.get("startjaar")
            eind_raw = regel.get("eindjaar")
            inflatie_raw = regel.get("inflatie_pct", 0)
        else:
            sleutel_raw = getattr(regel, "sleutel", None)
            waarde_raw = getattr(regel, "waarde", None)
            start_raw = getattr(regel, "startjaar", None)
            eind_raw = getattr(regel, "eindjaar", None)
            inflatie_raw = getattr(regel, "inflatie_pct", 0)

        sleutel = str(sleutel_raw).strip()
        if not sleutel:
            return None
        return TariefPeriodeRegel(
            sleutel=sleutel,
            waarde=Decimal(str(waarde_raw)),
            startjaar=int(start_raw) if start_raw is not None else None,
            eindjaar=int(eind_raw) if eind_raw is not None else None,
            inflatie_pct=Decimal(str(inflatie_raw)),
        )
    except (TypeError, ValueError, AttributeError):
        return None


def resolve_tariefwaarden_voor_jaar(
    config: BelastingConfig,
    jaar: int,
    periode_regels: list[Any],
) -> tuple[BelastingConfig, dict[str, str]]:
    """Los tariefperiode-regels op voor een jaar met gap/overlap-regels en inflatie."""
    basis = config_naar_tariefwaarden(config)
    regels: list[TariefPeriodeRegel] = []
    for r in periode_regels:
        p = _parse_periode_regel(r)
        if p is not None:
            regels.append(p)

    bronnen: dict[str, str] = {k: "basisconfig" for k in basis.keys()}
    opgelost = dict(basis)

    for sleutel, basiswaarde in basis.items():
        relevante = [r for r in regels if r.sleutel == sleutel]
        if not relevante:
            continue

        matches = [
            r for r in relevante
            if (r.startjaar is None or r.startjaar <= jaar)
            and (r.eindjaar is None or r.eindjaar >= jaar)
        ]

        gekozen: TariefPeriodeRegel | None = None
        bron = "basisconfig"
        if matches:
            gekozen = matches[-1]  # overlap: laatst opgegeven wint
            bron = "periode-match"
        else:
            historische = [r for r in relevante if r.startjaar is not None and r.startjaar <= jaar]
            if historische:
                historische.sort(key=lambda r: r.startjaar or -10**9)
                gekozen = historische[-1]
                bron = "hiaat-doorrol (laatst geldend)"

        if gekozen is None:
            opgelost[sleutel] = basiswaarde
            bronnen[sleutel] = bron
            continue

        startjaar = gekozen.startjaar if gekozen.startjaar is not None else jaar
        jaren_delta = max(0, jaar - startjaar)
        factor = (Decimal("1") + (gekozen.inflatie_pct / Decimal("100"))) ** jaren_delta
        opgelost[sleutel] = gekozen.waarde * factor
        bronnen[sleutel] = (
            f"{bron}: {gekozen.startjaar or 'begin'}-{gekozen.eindjaar or 'einde'}"
            f", inflatie {gekozen.inflatie_pct}%"
        )

    return pas_tariefwaarden_toe_op_config(config, opgelost), bronnen
