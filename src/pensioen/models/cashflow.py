"""Datamodellen voor cashflow-resultaten per maand en per jaar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pensioen.models.output_contract import AccountantDetailDTO, JaarSamenvattingDTO


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
    vermogen_correctie: Decimal = Decimal("0")  # Nieuw bekende saldostand; geen inkomen/inleg.

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
        """Vrije cashflow na belasting, uitgaven en incidentele posten."""
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

    @property
    def netto_inkomen(self) -> Decimal:
        """Netto inkomen vóór box 3, huishoudelijke en incidentele uitgaven."""
        return (
            self.totaal_bruto
            + self.inkomen_componenten_netto
            - self.belasting_p1
            - self.belasting_p2
            + self.totaal_heffingskorting
            - self.inhoudingen
        )


@dataclass
class BrutoInkomenPersoon:
    """Expliciete opbouw van bruto inkomen per persoon."""

    arbeid: Decimal = Decimal("0")
    aow: Decimal = Decimal("0")
    pensioen: Decimal = Decimal("0")
    overig: Decimal = Decimal("0")

    @property
    def totaal(self) -> Decimal:
        return self.arbeid + self.aow + self.pensioen + self.overig


@dataclass
class BrutoInkomenJaar:
    """Expliciete bruto-inkomensopbouw voor een huishouden in één jaar."""

    p1: BrutoInkomenPersoon = field(default_factory=BrutoInkomenPersoon)
    p2: BrutoInkomenPersoon = field(default_factory=BrutoInkomenPersoon)

    @property
    def totaal_huishouden(self) -> Decimal:
        return self.p1.totaal + self.p2.totaal


@dataclass
class JaarResultaat:
    """Geaggregeerd resultaat voor één kalenderjaar."""

    jaar: int
    maanden: list[MaandResultaat] = field(default_factory=list)
    tarieven_jaar: int = 0  # welk belastingjaar daadwerkelijk gebruikt
    tarieven_aanname: str = ""  # melding als toekomstig jaar
    bruto_inkomen: BrutoInkomenJaar = field(default_factory=BrutoInkomenJaar)
    jaar_samenvatting: JaarSamenvattingDTO = field(default_factory=dict)
    accountant_detail: AccountantDetailDTO = field(default_factory=dict)

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
    def overig_bruto(self) -> Decimal:
        """Overig bruto inkomen (alleen OVERIG_INKOMEN componenten, geen PENSIOEN_INKOMEN)."""
        return sum(m.overig_bruto for m in self.maanden)

    @property
    def inkomen_bruto(self) -> Decimal:
        """
        Totaal bruto inkomen (excl. rendement/rente).
        
        Dit is de som van alle inkomensbronnen: arbeidsinkomen, AOW, pensioen en overig inkomen.
        Rendement op vermogen wordt NIET als inkomen beschouwd.
        
        Returns:
            Som van arbeid_bruto + aow_bruto + pensioen_bruto + overig_bruto
        """
        return self.arbeid_bruto + self.aow_bruto + self.pensioen_bruto + self.overig_bruto
    
    @property
    def inkomen_bronnen(self) -> dict[str, Decimal]:
        """
        Breakdown van bruto inkomen per bron (excl. rendement).
        
        Handig voor grafieken en rapporten die inkomstenbronnen willen tonen.
        
        Returns:
            Dict met keys: "Arbeidsinkomen", "AOW", "Pensioen", "Overig inkomen"
        """
        return {
            "Arbeidsinkomen": self.arbeid_bruto,
            "AOW": self.aow_bruto,
            "Pensioen": self.pensioen_bruto,
            "Overig inkomen": self.overig_bruto,
        }
    
    @property
    def rendement_bruto(self) -> Decimal:
        """
        Rendement op vermogen (rente).
        
        Dit is het verschil tussen totaal_bruto en inkomen_bruto.
        
        Returns:
            totaal_bruto - inkomen_bruto
        """
        return self.totaal_bruto - self.inkomen_bruto

    @property
    def totaal_bruto(self) -> Decimal:
        return sum(m.totaal_bruto for m in self.maanden)

    @property
    def totaal_belasting(self) -> Decimal:
        return sum(m.totaal_belasting for m in self.maanden)

    @property
    def box1_belasting(self) -> Decimal:
        """Box 1 belasting (totaal_belasting min box3)."""
        return sum((m.belasting_p1 + m.belasting_p2) for m in self.maanden)

    @property
    def box3_heffing(self) -> Decimal:
        """Box 3 vermogensbelasting."""
        return sum(m.box3_heffing for m in self.maanden)

    @property
    def totaal_heffingskorting(self) -> Decimal:
        return sum(m.totaal_heffingskorting for m in self.maanden)

    @property
    def inhoudingen(self) -> Decimal:
        """Totale inhoudingen (loonheffing, premies, etc.)."""
        return sum(m.inhoudingen for m in self.maanden)

    @property
    def huishoudelijke_uitgaven(self) -> Decimal:
        """Totale jaarlijkse huishoudelijke uitgaven."""
        return sum(m.huishoudelijke_uitgaven for m in self.maanden)

    @property
    def eenmalige_uitgaven(self) -> Decimal:
        """Totale eenmalige uitgaven dit jaar."""
        return sum(m.eenmalig_uitgave for m in self.maanden)

    @property
    def eenmalige_ontvangsten(self) -> Decimal:
        """Totale eenmalige ontvangsten dit jaar."""
        return sum(m.eenmalig_ontvangst for m in self.maanden)

    @property
    def netto(self) -> Decimal:
        return sum(m.netto for m in self.maanden)

    @property
    def netto_inkomen(self) -> Decimal:
        return sum(m.netto_inkomen for m in self.maanden)

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
