"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from pensioen.models.component import CategorieComponent, FinancieelComponent
from pensioen.models.vermogensitem import VermogensItem, VermogensType


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

    # Spaargeld en rendement (LEGACY: zie vermogensitems voor nieuwe structuur)
    spaargeld_start: Decimal = Decimal("0")   # beginsaldo in euro's
    beleggingen_start: Decimal = Decimal("0")  # beginwaarde beleggingen in euro's
    jaarlijkse_inleg: Decimal = Decimal("0")  # DEPRECATED: gebruik jaarlijkse_inleg_sparen + jaarlijkse_inleg_beleggen
    jaarlijkse_inleg_sparen: Decimal = Decimal("0")    # jaarlijkse toevoeging aan spaargeld
    jaarlijkse_inleg_beleggen: Decimal = Decimal("0")  # jaarlijkse toevoeging aan beleggingen
    rendement_pct: Decimal = Decimal("3")     # verwacht jaarlijks rendement in %
    rendement_sparen_pct: Decimal | None = None    # rendement op spaargeld (als None: gebruik rendement_pct)
    rendement_beleggen_pct: Decimal | None = None  # rendement op beleggingen (als None: gebruik rendement_pct)

    # Vermogensitems (nieuwe structuur voor spaargeld, beleggingen en overige bezittingen)
    vermogensitems: list[VermogensItem] = Field(default_factory=list)

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
    
    def totaal_jaarlijkse_inleg(self) -> Decimal:
        """Retourneer totale jaarlijkse inleg (sparen + beleggen)."""
        # Backward compatibility: als oude jaarlijkse_inleg is ingesteld, gebruik die
        if self.jaarlijkse_inleg > Decimal("0") and self.jaarlijkse_inleg_sparen == Decimal("0") and self.jaarlijkse_inleg_beleggen == Decimal("0"):
            return self.jaarlijkse_inleg
        return self.jaarlijkse_inleg_sparen + self.jaarlijkse_inleg_beleggen

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
        
        # Tel cumulatieve inleg op tot peildatum (jaren * maanden)
        jaren_sinds_start = peildatum.year - date.today().year
        maanden_sinds_start = max(0, jaren_sinds_start * 12 + (peildatum.month - date.today().month))
        
        if maanden_sinds_start > 0:
            inleg_sparen_totaal = (self.jaarlijkse_inleg_sparen / Decimal("12")) * Decimal(str(maanden_sinds_start))
            inleg_beleggen_totaal = (self.jaarlijkse_inleg_beleggen / Decimal("12")) * Decimal(str(maanden_sinds_start))
            saldo_sparen += inleg_sparen_totaal
            saldo_beleggen += inleg_beleggen_totaal
        
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
    
    def migreer_legacy_vermogen(self) -> None:
        """
        Migreer oude spaargeld_start en beleggingen_start naar vermogensitems.
        
        Maakt VermogensItem entries aan voor spaargeld en beleggingen indien deze
        nog niet bestaan in vermogensitems lijst.
        
        Deze method wordt aangeroepen bij het laden van oude sessies om backward
        compatibility te waarborgen.
        """
        # Check of er al spaargeld/beleggingen items zijn
        heeft_spaargeld = any(v.type == VermogensType.SPAARGELD for v in self.vermogensitems)
        heeft_beleggingen = any(v.type == VermogensType.BELEGGINGEN for v in self.vermogensitems)
        
        # Migreer spaargeld als dit nog niet bestaat
        if not heeft_spaargeld and self.spaargeld_start > Decimal("0"):
            spaargeld_item = VermogensItem(
                omschrijving="Spaargeld (gemigreerd)",
                type=VermogensType.SPAARGELD,
                persoon="Huishouden",
                aanschafwaarde=self.spaargeld_start,
                groei_pct=self.get_rendement_sparen(),
                box3_belast=True,
            )
            self.vermogensitems.append(spaargeld_item)
        
        # Migreer beleggingen als dit nog niet bestaat
        if not heeft_beleggingen and self.beleggingen_start > Decimal("0"):
            beleggingen_item = VermogensItem(
                omschrijving="Beleggingen (gemigreerd)",
                type=VermogensType.BELEGGINGEN,
                persoon="Huishouden",
                aanschafwaarde=self.beleggingen_start,
                groei_pct=self.get_rendement_beleggen(),
                box3_belast=True,
            )
            self.vermogensitems.append(beleggingen_item)
    
    def totaal_vermogen_op_datum(self, peildatum: date) -> Decimal:
        """
        Bereken totaal vermogen op een specifieke datum.
        
        Som van alle actieve vermogensitems (inclusief gemigreerde legacy spaargeld/beleggingen).
        
        Args:
            peildatum: Datum waarop vermogen wordt berekend.
        
        Returns:
            Totaal vermogen in euro's.
        """
        # Zorg dat legacy vermogen gemigreerd is
        if not self.vermogensitems and (self.spaargeld_start > Decimal("0") or self.beleggingen_start > Decimal("0")):
            self.migreer_legacy_vermogen()
        
        totaal = Decimal("0")
        for item in self.vermogensitems:
            totaal += item.waarde_op_datum(peildatum)
        
        return totaal
    
    def get_vermogensitems_actief(self, peildatum: date) -> list[VermogensItem]:
        """
        Geef lijst van actieve vermogensitems op een specifieke datum.
        
        Args:
            peildatum: Datum waarop items actief moeten zijn.
        
        Returns:
            Lijst van actieve VermogensItems.
        """
        # Zorg dat legacy vermogen gemigreerd is
        if not self.vermogensitems and (self.spaargeld_start > Decimal("0") or self.beleggingen_start > Decimal("0")):
            self.migreer_legacy_vermogen()
        
        return [item for item in self.vermogensitems if item.is_actief_op(peildatum)]
    
    def get_vermogensitems_box3_belast(self, peildatum: date) -> list[VermogensItem]:
        """
        Geef lijst van box 3 belaste vermogensitems op een specifieke datum.
        
        Args:
            peildatum: Datum waarop items actief moeten zijn.
        
        Returns:
            Lijst van actieve, box 3 belaste VermogensItems.
        """
        actieve_items = self.get_vermogensitems_actief(peildatum)
        return [item for item in actieve_items if item.box3_belast]
