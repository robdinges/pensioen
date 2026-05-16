"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from pensioen.models.component import CategorieComponent, FinancieelComponent


class IncidenteelItem(BaseModel):
    """Een eenmalige ontvangst (positief) of uitgave (negatief) op een specifieke datum."""

    datum: date
    bedrag: Decimal  # positief = ontvangst, negatief = uitgave
    omschrijving: str


class TariefPeriodeItem(BaseModel):
    """Periode-override voor één tariefsleutel."""

    sleutel: str
    startjaar: int | None = None
    eindjaar: int | None = None
    waarde: Decimal
    inflatie_pct: Decimal = Decimal("0")


class Scenario(BaseModel):
    """Een planningsscenario met parameters voor cashflowberekeningen."""

    naam: str  # korte naam voor keuzelijsten
    omschrijving: str = ""
    aangemaakt_op: datetime = Field(default_factory=datetime.now)
    laatst_gewijzigd_op: datetime = Field(default_factory=datetime.now)
    is_default: bool = False

    # Spaargeld en rendement
    spaargeld_start: Decimal = Decimal("0")   # beginsaldo in euro's
    beleggingen_start: Decimal = Decimal("0")  # beginwaarde beleggingen in euro's
    jaarlijkse_inleg: Decimal = Decimal("0")  # jaarlijkse toevoeging aan vermogen
    rendement_pct: Decimal = Decimal("3")     # verwacht jaarlijks rendement in %
    rendement_sparen_pct: Decimal | None = None    # rendement op spaargeld (als None: gebruik rendement_pct)
    rendement_beleggen_pct: Decimal | None = None  # rendement op beleggingen (als None: gebruik rendement_pct)

    # Financiële componenten (inkomsten, uitgaven, inhoudingen)
    componenten: list[FinancieelComponent] = []

    # Incidentele eenmalige cashflows (niet belastbaar)
    incidentele_items: list[IncidenteelItem] = []

    # Inflatie
    inflatie_pct: Decimal = Decimal("2")  # verwachte jaarlijkse inflatie in %

    # Box 3
    box3_meenemen: bool = True
    box3_spaargeld_fractie: Decimal = Decimal("1")  # 0=beleggingen, 1=spaargeld

    # Periodegebaseerde tariefoverrides
    tarief_periodes: list[TariefPeriodeItem] = []

    @model_validator(mode="after")
    def valideer_bedragen(self) -> Scenario:
        if self.spaargeld_start < Decimal("0"):
            raise ValueError("spaargeld_start mag niet negatief zijn.")
        if self.beleggingen_start < Decimal("0"):
            raise ValueError("beleggingen_start mag niet negatief zijn.")
        if not (Decimal("0") <= self.rendement_pct <= Decimal("30")):
            raise ValueError("rendement_pct moet tussen 0% en 30% liggen.")
        if self.rendement_sparen_pct is not None and not (Decimal("0") <= self.rendement_sparen_pct <= Decimal("30")):
            raise ValueError("rendement_sparen_pct moet tussen 0% en 30% liggen.")
        if self.rendement_beleggen_pct is not None and not (Decimal("0") <= self.rendement_beleggen_pct <= Decimal("30")):
            raise ValueError("rendement_beleggen_pct moet tussen 0% en 30% liggen.")
        if not (Decimal("0") <= self.inflatie_pct <= Decimal("20")):
            raise ValueError("inflatie_pct moet tussen 0% en 20% liggen.")
        for p in self.tarief_periodes:
            if p.startjaar is not None and p.eindjaar is not None and p.eindjaar < p.startjaar:
                raise ValueError("Bij tarief_periodes moet eindjaar >= startjaar zijn.")
            if not (Decimal("0") <= p.inflatie_pct <= Decimal("20")):
                raise ValueError("inflatie_pct in tarief_periodes moet tussen 0% en 20% liggen.")
        return self

    def get_rendement_sparen(self) -> Decimal:
        """Geef rendement voor spaargeld; fallback naar rendement_pct als niet expliciet gezet."""
        return self.rendement_sparen_pct if self.rendement_sparen_pct is not None else self.rendement_pct

    def get_rendement_beleggen(self) -> Decimal:
        """Geef rendement voor beleggingen; fallback naar rendement_pct als niet expliciet gezet."""
        return self.rendement_beleggen_pct if self.rendement_beleggen_pct is not None else self.rendement_pct

    def totaal_vermogen_start(self) -> Decimal:
        """Totaal startvermogen (spaargeld + beleggingen)."""
        return self.spaargeld_start + self.beleggingen_start

    # --- Hulpeigenschappen voor terugwaartse compatibiliteit in rapportages ---
    def arbeidsinkomen_componenten(self, persoon: str) -> list[FinancieelComponent]:
        return [c for c in self.componenten
                if c.categorie == CategorieComponent.ARBEIDSINKOMEN and c.persoon == persoon]

    def inkomen_componenten(self, persoon: str) -> list[FinancieelComponent]:
        """Alle inkomenscategorieën voor een persoon (arbeid + pensioen + overig)."""
        return [c for c in self.componenten
                if c.categorie in (
                    CategorieComponent.ARBEIDSINKOMEN,
                    CategorieComponent.PENSIOEN_INKOMEN,
                    CategorieComponent.OVERIG_INKOMEN,
                ) and c.persoon == persoon]

    def uitgave_componenten(self) -> list[FinancieelComponent]:
        return [c for c in self.componenten if c.categorie == CategorieComponent.UITGAVE]

    def inhouding_componenten(self) -> list[FinancieelComponent]:
        return [c for c in self.componenten if c.categorie == CategorieComponent.INHOUDING]

    def bereken_spaargeld_fractie_op_datum(self, peildatum: date) -> Decimal:
        """
        Bereken de fractie van het totale vermogen dat spaargeld is (0-1) op basis van actieve componenten.
        
        Kijkt naar alle vermogencomponenten (inkomsten, uitgaven, inhoudingen) die actief zijn
        op de gegeven peildatum en bepaalt wat % ervan is gemarkeerd als SPAREN vs BELEGGEN.
        
        Args:
            peildatum: De datum waarop de fractie berekend moet worden.
            
        Returns:
            Fractie tussen 0 en 1. 1.0 = 100% spaargeld, 0.0 = 100% beleggingen.
        """
        from pensioen.models.component import BeleggingsType
        
        jaar = peildatum.year
        maand = peildatum.month
        
        # Start vanuit expliciet opgegeven beginverdeling.
        saldo_sparen = self.spaargeld_start
        saldo_beleggen = self.beleggingen_start
        
        for comp in self.componenten:
            if not comp.is_actief(jaar, maand):
                continue
                
            bedrag_maand = comp.bedrag_per_maand_actief(jaar, maand)
            
            # Negatieve bedragen (uitgaven/inhoudingen) tellen als aftrekking
            if comp.categorie in (CategorieComponent.UITGAVE, CategorieComponent.INHOUDING):
                bedrag_maand = -bedrag_maand
            
            if bedrag_maand == Decimal("0"):
                continue
            
            # Verdeel bedrag naar type
            if comp.beleggings_type == BeleggingsType.SPAREN:
                saldo_sparen += bedrag_maand
            else:  # BeleggingsType.BELEGGEN
                saldo_beleggen += bedrag_maand
        
        totaal = saldo_sparen + saldo_beleggen
        
        # Als er geen componenten zijn, gebruik de scenario-instelling
        if totaal == Decimal("0"):
            return self.box3_spaargeld_fractie
        
        # Fractie spaargeld
        fractie_sparen = saldo_sparen / totaal if totaal > Decimal("0") else Decimal("1")
        
        # Zorg dat fractie tussen 0 en 1 ligt
        return max(Decimal("0"), min(Decimal("1"), fractie_sparen))
