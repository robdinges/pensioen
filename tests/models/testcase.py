"""Pydantic models voor testcase validatie.

Deze models valideren de genormaliseerde testcase JSONs
en maken ze klaar voor conversie naar Scenario objecten.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class HuishoudType(str, Enum):
    """Type huishouden voor belastingdoeleinden."""
    
    ALLEENSTAAND = "ALLEENSTAAND"
    PAAR = "PAAR"
    GEHUWD = "GEHUWD"


class DataKwaliteit(str, Enum):
    """Niveau van detail in verwachte belasting."""
    
    MINIMAAL = "minimaal"  # alleen totaal_verschuldigd
    GEDEELTELIJK = "gedeeltelijk"  # Box 1/Box 3 totalen
    VOLLEDIG = "volledig"  # alle tussenresultaten


class TestHuishouden(BaseModel):
    """Huishouden configuratie."""
    
    type: HuishoudType
    aantal_personen: int = Field(ge=1, le=2)
    is_gehuwd: bool | None = None
    eigen_huis: bool = False
    
    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: Any) -> str:
        """Normaliseer huishoud type naar uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v


class TestPersoon(BaseModel):
    """Persoon binnen testcase."""
    
    naam: str
    geboortedatum: date
    
    # Inkomens (bruto jaarbedragen)
    bruto_arbeid: Decimal = Decimal("0")
    bruto_pensioen: Decimal = Decimal("0")
    bruto_aow: Decimal = Decimal("0")
    bruto_overig: Decimal = Decimal("0")
    
    # Optionele metadata
    is_aow_heel_jaar: bool | None = None
    
    @field_validator("geboortedatum", mode="before")
    @classmethod
    def parse_datum(cls, v: Any) -> date:
        """Parse datum uit verschillende formaten."""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        raise ValueError(f"Ongeldige datum: {v}")
    
    @property
    def totaal_bruto_inkomen(self) -> Decimal:
        """Totaal bruto inkomen."""
        return (
            self.bruto_arbeid + 
            self.bruto_pensioen + 
            self.bruto_aow + 
            self.bruto_overig
        )


class TestVermogen(BaseModel):
    """Vermogen configuratie."""
    
    totaal: Decimal
    spaargeld_fractie: Decimal = Field(default=Decimal("0.4"), ge=0, le=1)
    
    # Optionele absolute bedragen
    spaargeld: Decimal | None = None
    beleggingen: Decimal | None = None
    verdeling_personen: dict[str, Any] | None = None  # flexibel voor P1/P2 verdeling
    
    # Pydantic config
    model_config = {"extra": "allow"}
    
    @property
    def spaargeld_berekend(self) -> Decimal:
        """Bereken spaargeld bedrag."""
        if self.spaargeld is not None:
            return self.spaargeld
        return self.totaal * self.spaargeld_fractie
    
    @property
    def beleggingen_berekend(self) -> Decimal:
        """Bereken beleggingen bedrag."""
        if self.beleggingen is not None:
            return self.beleggingen
        return self.totaal * (Decimal("1") - self.spaargeld_fractie)


class TestVerwachteBelasting(BaseModel):
    """Verwachte belasting uitkomst (flexibel schema).
    
    Verplicht: totaal_verschuldigd (huishouden-totaal)
    Optioneel: alle tussenresultaten voor validatie
    """
    
    # Verplicht: huishouden-totaal
    totaal_verschuldigd: Decimal
    
    # Optioneel: per persoon totalen (p1/p2 suffix)
    totaal_verschuldigd_p1: Decimal | None = None
    totaal_verschuldigd_p2: Decimal | None = None
    
    # Optioneel: alle andere velden (flexibel schema)
    # Box 1
    bruto_p1: Decimal | None = None
    bruto_p2: Decimal | None = None
    box1_ib_p1: Decimal | None = None
    box1_ib_p2: Decimal | None = None
    box1_schijf1_p1: Decimal | None = None
    box1_schijf2_p1: Decimal | None = None
    box1_schijf3_p1: Decimal | None = None
    box1_schijf1_p2: Decimal | None = None
    box1_schijf2_p2: Decimal | None = None
    box1_schijf3_p2: Decimal | None = None
    
    # Premies
    premie_aow_p1: Decimal | None = None
    premie_anw_p1: Decimal | None = None
    premie_wlz_p1: Decimal | None = None
    totaal_premies_p1: Decimal | None = None
    premie_aow_p2: Decimal | None = None
    premie_anw_p2: Decimal | None = None
    premie_wlz_p2: Decimal | None = None
    totaal_premies_p2: Decimal | None = None
    
    # Heffingskortingen
    ahk_p1: Decimal | None = None
    arbeidskorting_p1: Decimal | None = None
    ouderenkorting_p1: Decimal | None = None
    ahk_p2: Decimal | None = None
    arbeidskorting_p2: Decimal | None = None
    ouderenkorting_p2: Decimal | None = None
    alleenstaandeouderenkorting: Decimal | None = None
    totaal_kortingen: Decimal | None = None
    totaal_kortingen_p1: Decimal | None = None
    totaal_kortingen_p2: Decimal | None = None
    
    # Box 3
    box3_vrijstelling: Decimal | None = None
    box3_grondslag: Decimal | None = None
    box3_grondslag_p1: Decimal | None = None
    box3_grondslag_p2: Decimal | None = None
    box3_fictief_rendement: Decimal | None = None
    box3_heffing: Decimal | None = None
    box3_heffing_p1: Decimal | None = None
    box3_heffing_p2: Decimal | None = None
    
    # Totalen
    totaal_ib_en_premies: Decimal | None = None
    totaal_ib_en_premies_p1: Decimal | None = None
    totaal_ib_en_premies_p2: Decimal | None = None
    
    # Extra flexibiliteit voor onverwachte velden
    model_config = {"extra": "allow"}


class TestMetadata(BaseModel):
    """Metadata over testcase."""
    
    uitgangspunten: list[str] = Field(default_factory=list)
    opmerkingen: str = ""
    data_kwaliteit: DataKwaliteit = DataKwaliteit.MINIMAAL
    bron: str = ""
    _incomplete: bool = False
    
    # Extra flexibiliteit
    model_config = {"extra": "allow"}


class EigenWoningTestData(BaseModel):
    """Gestructureerde eigen woning gegevens voor testcase."""

    woz_waarde: Decimal = Decimal("0")
    betaalde_hypotheekrente: Decimal = Decimal("0")
    overige_aftrekbare_kosten: Decimal = Decimal("0")
    eigenwoningschuld_begin: Decimal = Decimal("0")
    eigenwoningschuld_eind: Decimal = Decimal("0")


class TestCase(BaseModel):
    """Complete testcase voor belasting validatie.
    
    Dit model valideert de genormaliseerde testcase JSONs
    en biedt type-safe toegang tot alle velden.
    """
    
    testcase_id: str
    naam: str
    jaar: int = Field(ge=2020, le=2030)
    
    # Optionele root metadata
    datum_aangeleverd: str | None = None
    bron_formaat: str | None = None
    
    # Core data
    huishouden: TestHuishouden
    personen: list[TestPersoon] = Field(min_length=1, max_length=2)
    vermogen: TestVermogen
    verwachte_belasting: TestVerwachteBelasting
    eigen_woning: EigenWoningTestData | None = None
    metadata: TestMetadata = Field(default_factory=TestMetadata)
    
    @field_validator("personen")
    @classmethod
    def valideer_aantal_personen(cls, v: list[TestPersoon], info) -> list[TestPersoon]:
        """Controleer dat aantal personen consistent is."""
        # info.data bevat de al gevalideerde velden
        if "huishouden" in info.data:
            huishouden = info.data["huishouden"]
            if hasattr(huishouden, "aantal_personen"):
                if len(v) != huishouden.aantal_personen:
                    raise ValueError(
                        f"Aantal personen ({len(v)}) komt niet overeen met "
                        f"huishouden.aantal_personen ({huishouden.aantal_personen})"
                    )
        return v
    
    @property
    def is_alleenstaand(self) -> bool:
        """Check of dit een alleenstaand huishouden is."""
        return self.huishouden.type == HuishoudType.ALLEENSTAAND
    
    @property
    def is_paar(self) -> bool:
        """Check of dit een paar/gehuwd huishouden is."""
        return self.huishouden.type in (HuishoudType.PAAR, HuishoudType.GEHUWD)
    
    @property
    def heeft_eigen_huis(self) -> bool:
        """Check of huishouden eigen huis heeft."""
        return self.huishouden.eigen_huis
    
    @property
    def totaal_bruto_inkomen_huishouden(self) -> Decimal:
        """Totaal bruto inkomen van alle personen."""
        return sum(p.totaal_bruto_inkomen for p in self.personen)
