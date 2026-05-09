"""Datamodellen voor cashflow-resultaten per maand en per jaar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class MaandResultaat:
    """Berekend resultaat voor één kalendermaand van het huishouden."""

    jaar: int
    maand: int  # 1–12

    # Bruto inkomstenbronnen in euro's
    arbeid_p1_bruto: Decimal = Decimal("0")
    arbeid_p2_bruto: Decimal = Decimal("0")
    aow_p1_bruto: Decimal = Decimal("0")
    aow_p2_bruto: Decimal = Decimal("0")
    pensioen_p1_bruto: Decimal = Decimal("0")
    pensioen_p2_bruto: Decimal = Decimal("0")
    lijfrente_bruto: Decimal = Decimal("0")
    rente_bruto: Decimal = Decimal("0")
    overig_bruto: Decimal = Decimal("0")
    inkomen_componenten_netto: Decimal = Decimal("0")

    # Eenmalige items (exacte datumplaatsing)
    eenmalig_ontvangst: Decimal = Decimal("0")
    eenmalig_uitgave: Decimal = Decimal("0")

    # Belasting per persoon (jaarbelasting / 12)
    belasting_p1: Decimal = Decimal("0")
    heffingskorting_p1: Decimal = Decimal("0")
    belasting_p2: Decimal = Decimal("0")
    heffingskorting_p2: Decimal = Decimal("0")
    box3_heffing: Decimal = Decimal("0")

    # Overige inhoudingen en uitgaven (jaarlijkse regels omgerekend naar maand)
    inhoudingen: Decimal = Decimal("0")
    huishoudelijke_uitgaven: Decimal = Decimal("0")

    # Vermogen
    vermogen_einde_maand: Decimal = Decimal("0")

    # Transparantie
    aannames: list[str] = field(default_factory=list)
    gebruikte_tarieven: dict = field(default_factory=dict)

    @property
    def totaal_bruto(self) -> Decimal:
        return (
            self.arbeid_p1_bruto
            + self.arbeid_p2_bruto
            + self.aow_p1_bruto
            + self.aow_p2_bruto
            + self.pensioen_p1_bruto
            + self.pensioen_p2_bruto
            + self.lijfrente_bruto
            + self.rente_bruto
            + self.overig_bruto
        )

    @property
    def totaal_belasting(self) -> Decimal:
        return self.belasting_p1 + self.belasting_p2 + self.box3_heffing

    @property
    def totaal_heffingskorting(self) -> Decimal:
        return self.heffingskorting_p1 + self.heffingskorting_p2

    @property
    def netto(self) -> Decimal:
        return (
            self.totaal_bruto
            + self.inkomen_componenten_netto
            - self.totaal_belasting
            + self.totaal_heffingskorting
            - self.inhoudingen
            - self.huishoudelijke_uitgaven
            + self.eenmalig_ontvangst
            - self.eenmalig_uitgave
        )


@dataclass
class JaarResultaat:
    """Geaggregeerd resultaat voor één kalenderjaar."""

    jaar: int
    maanden: list[MaandResultaat] = field(default_factory=list)
    tarieven_jaar: int = 0  # welk belastingjaar daadwerkelijk gebruikt
    tarieven_aanname: str = ""  # melding als toekomstig jaar

    @property
    def arbeid_bruto(self) -> Decimal:
        return sum(m.arbeid_p1_bruto + m.arbeid_p2_bruto for m in self.maanden)

    @property
    def aow_bruto(self) -> Decimal:
        return sum(m.aow_p1_bruto + m.aow_p2_bruto for m in self.maanden)

    @property
    def pensioen_bruto(self) -> Decimal:
        return sum(m.pensioen_p1_bruto + m.pensioen_p2_bruto for m in self.maanden)

    @property
    def totaal_bruto(self) -> Decimal:
        return sum(m.totaal_bruto for m in self.maanden)

    @property
    def totaal_belasting(self) -> Decimal:
        return sum(m.totaal_belasting for m in self.maanden)

    @property
    def totaal_heffingskorting(self) -> Decimal:
        return sum(m.totaal_heffingskorting for m in self.maanden)

    @property
    def netto(self) -> Decimal:
        return sum(m.netto for m in self.maanden)

    @property
    def netto_per_maand(self) -> Decimal:
        if not self.maanden:
            return Decimal("0")
        return self.netto / Decimal(str(len(self.maanden)))

    @property
    def effectief_tarief(self) -> Decimal:
        """Effectief belastingtarief als percentage van bruto inkomen."""
        if self.totaal_bruto == Decimal("0"):
            return Decimal("0")
        netto_belasting = self.totaal_belasting - self.totaal_heffingskorting
        return max(
            Decimal("0"),
            netto_belasting / self.totaal_bruto * Decimal("100"),
        )

    @property
    def is_tekortjaar(self) -> bool:
        return self.netto < Decimal("0")

    @property
    def vermogen_einde_jaar(self) -> Decimal:
        if not self.maanden:
            return Decimal("0")
        return self.maanden[-1].vermogen_einde_maand


@dataclass
class HuishoudCashflow:
    """Totale cashflowprognose voor het huishouden over meerdere jaren."""

    scenario_naam: str
    jaren: list[JaarResultaat] = field(default_factory=list)
    aannames: list[str] = field(default_factory=list)

    @property
    def laagste_inkomensjaar(self) -> JaarResultaat | None:
        if not self.jaren:
            return None
        return min(self.jaren, key=lambda j: j.netto)

    @property
    def tekortjaren(self) -> list[JaarResultaat]:
        return [j for j in self.jaren if j.is_tekortjaar]

    def vermogen_op_leeftijd(
        self, geboortedatum_persoon1: date, leeftijd: int
    ) -> Decimal:
        """Vermogen aan het einde van het jaar waarin persoon1 de gewenste leeftijd bereikt."""
        doeljaar = geboortedatum_persoon1.year + leeftijd
        voor_jaar = [j for j in self.jaren if j.jaar == doeljaar]
        if not voor_jaar:
            return Decimal("0")
        return voor_jaar[0].vermogen_einde_jaar
