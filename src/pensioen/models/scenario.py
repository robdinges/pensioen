"""Datamodel voor een planningsscenario."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from pensioen.models.component import CategorieComponent, FinancieelComponent
from pensioen.models.vermogensitem import VermogensItem, VermogensType


class IncidenteelItem(BaseModel):
    """Een eenmalige ontvangst (positief) of uitgave (negatief) op een specifieke datum."""

    datum: date
    bedrag: Decimal  # positief = ontvangst, negatief = uitgave
    omschrijving: str


class EigenWoningData(BaseModel):
    """Eigen woning gegevens per scenario (jaarlijkse bedragen)."""

    woz_waarde: Decimal = Decimal("0")
    betaalde_hypotheekrente: Decimal = Decimal("0")
    overige_aftrekbare_kosten: Decimal = Decimal("0")
    eigenwoningschuld_begin: Decimal = Decimal("0")
    eigenwoningschuld_eind: Decimal = Decimal("0")


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

    # Inheritance: afgeleid scenario (parent-child relatie)
    parent_naam: str | None = None  # naam van parent scenario (None = base scenario)
    overrides: dict[str, Any] = Field(default_factory=dict)  # sparse storage van gewijzigde velden

    # Spaargeld en rendement (LEGACY: zie vermogensitems voor nieuwe structuur)
    spaargeld_start: Decimal = Decimal("0")   # beginsaldo in euro's
    beleggingen_start: Decimal = Decimal("0")  # beginwaarde beleggingen in euro's
    jaarlijkse_inleg: Decimal = Decimal("0")  # DEPRECATED: gebruik jaarlijkse_inleg_sparen + jaarlijkse_inleg_beleggen
    jaarlijkse_inleg_sparen: Decimal = Decimal("0")    # jaarlijkse toevoeging aan spaargeld
    jaarlijkse_inleg_beleggen: Decimal = Decimal("0")  # jaarlijkse toevoeging aan beleggingen
    
    # DEPRECATED: rendement wordt nu per vermogensitem ingesteld (zie VermogensItem.groei_pct)
    # Behouden voor backward compatibility met oude sessies
    rendement_pct: Decimal | None = None     # DEPRECATED
    rendement_sparen_pct: Decimal | None = None    # DEPRECATED
    rendement_beleggen_pct: Decimal | None = None  # DEPRECATED

    # Vermogensitems (nieuwe structuur voor spaargeld, beleggingen en overige bezittingen)
    vermogensitems: list[VermogensItem] = Field(default_factory=list)

    # Financiële componenten (inkomsten, uitgaven, inhoudingen)
    componenten: list[FinancieelComponent] = []

    # Incidentele eenmalige cashflows (niet belastbaar)
    incidentele_items: list[IncidenteelItem] = []

    # Inflatie (voor koopkrachtberekening in rapportages)
    inflatie_pct: Decimal = Decimal("2")  # verwachte jaarlijkse inflatie in %

    # Box 3
    box3_meenemen: bool = True
    # DEPRECATED: box3 type wordt nu automatisch bepaald per VermogensItem
    box3_spaargeld_fractie: Decimal | None = None  # DEPRECATED

    # Periodegebaseerde tariefoverrides
    tarief_periodes: list[TariefPeriodeItem] = []

    # Eigen woning (box 1)
    heeft_eigen_woning: bool = False
    eigen_woning: EigenWoningData = Field(default_factory=EigenWoningData)

    @model_validator(mode="after")
    def valideer_bedragen(self) -> Scenario:
        if self.spaargeld_start < Decimal("0"):
            raise ValueError("spaargeld_start mag niet negatief zijn.")
        if self.beleggingen_start < Decimal("0"):
            raise ValueError("beleggingen_start mag niet negatief zijn.")
        for rendement in (self.rendement_pct, self.rendement_sparen_pct, self.rendement_beleggen_pct):
            if rendement is not None and (not rendement.is_finite() or rendement < Decimal("-100")):
                raise ValueError("Rendement moet eindig zijn en minimaal -100% bedragen.")
        if not (Decimal("0") <= self.inflatie_pct <= Decimal("20")):
            raise ValueError("inflatie_pct moet tussen 0% en 20% liggen.")
        for p in self.tarief_periodes:
            if p.startjaar is not None and p.eindjaar is not None and p.eindjaar < p.startjaar:
                raise ValueError("Bij tarief_periodes moet eindjaar >= startjaar zijn.")
            if not (Decimal("0") <= p.inflatie_pct <= Decimal("20")):
                raise ValueError("inflatie_pct in tarief_periodes moet tussen 0% en 20% liggen.")
        
        # Valideer inheritance: prevent self-parenting
        if self.parent_naam is not None and self.parent_naam == self.naam:
            raise ValueError(
                f"Scenario '{self.naam}' kan niet naar zichzelf als parent wijzen (self-parenting)."
            )
        
        return self

    def get_rendement_sparen(self) -> Decimal:
        """
        Geef rendement voor spaargeld (voor backward compatibility).
        
        DEPRECATED: Rendement wordt nu per vermogensitem ingesteld.
        Deze method gebruikt een fallback van 3% voor migratie van oude data.
        """
        if self.rendement_sparen_pct is not None:
            return self.rendement_sparen_pct
        if self.rendement_pct is not None:
            return self.rendement_pct
        return Decimal("3")  # Default fallback

    def get_rendement_beleggen(self) -> Decimal:
        """
        Geef rendement voor beleggingen (voor backward compatibility).
        
        DEPRECATED: Rendement wordt nu per vermogensitem ingesteld.
        Deze method gebruikt een fallback van 5% voor migratie van oude data.
        """
        if self.rendement_beleggen_pct is not None:
            return self.rendement_beleggen_pct
        if self.rendement_pct is not None:
            return self.rendement_pct
        return Decimal("5")  # Default fallback voor beleggingen

    def totaal_vermogen_start(self) -> Decimal:
        """Totaal startvermogen (spaargeld + beleggingen)."""
        return self.spaargeld_start + self.beleggingen_start

    def bereken_spaargeld_fractie_startvermogen(self, peildatum: date | None = None) -> Decimal:
        """Bereken spaargeldfractie voor box 3 op peildatum.

        Bronvolgorde:
        1) Actieve vermogensitems (box-3-belaste SPAARGELD/BELEGGINGEN) op peildatum.
        2) Legacy startvelden spaargeld_start/beleggingen_start.
        3) Legacy override box3_spaargeld_fractie.
        4) Veilige default 50/50.
        """
        if peildatum is None:
            peildatum = date.today()

        box3_spaargeld = Decimal("0")
        box3_overig = Decimal("0")
        for item in self.vermogensitems:
            if not item.box3_belast or not item.is_actief_op(peildatum):
                continue
            if item.type in (VermogensType.EIGEN_WONING, VermogensType.HYPOTHEEK):
                continue
            waarde = item.waarde_op_datum(peildatum)
            if item.type == VermogensType.SPAARGELD:
                box3_spaargeld += waarde
            else:
                box3_overig += waarde

        totaal_items = box3_spaargeld + box3_overig
        if totaal_items > Decimal("0"):
            return max(
                Decimal("0"),
                min(Decimal("1"), box3_spaargeld / totaal_items),
            )

        totaal_start = self.totaal_vermogen_start()
        if totaal_start > Decimal("0"):
            return max(
                Decimal("0"),
                min(Decimal("1"), self.spaargeld_start / totaal_start),
            )

        if self.box3_spaargeld_fractie is not None:
            return max(
                Decimal("0"),
                min(Decimal("1"), self.box3_spaargeld_fractie),
            )

        return Decimal("0.5")

    def bepaal_vermogen_startwaarden(self, peildatum: date) -> dict[str, Decimal | str]:
        """Bepaal startwaarden voor vermogen- en box3-stappen op peildatum.

        `vermogensitems` zijn leidend zodra er actieve liquide items of andere
        box-3-belaste items zijn. De box-3-grondslag wordt uitgesplitst in een
        liquide deel en vaste overige items. Bij afwezigheid van een formele
        vermogensbron geldt de legacy fallback.
        """
        liquide_spaargeld = Decimal("0")
        liquide_beleggingen = Decimal("0")
        box3_liquide_grondslag = Decimal("0")
        box3_vaste_grondslag = Decimal("0")

        for item in self.vermogensitems:
            if not item.is_actief_op(peildatum):
                continue

            waarde = item.waarde_op_datum(peildatum)
            if item.type == VermogensType.SPAARGELD:
                liquide_spaargeld += waarde
            elif item.type == VermogensType.BELEGGINGEN:
                liquide_beleggingen += waarde

            if not item.box3_belast or item.type in (
                VermogensType.EIGEN_WONING,
                VermogensType.HYPOTHEEK,
            ):
                continue
            if item.type in (VermogensType.SPAARGELD, VermogensType.BELEGGINGEN):
                box3_liquide_grondslag += waarde
            else:
                box3_vaste_grondslag += waarde

        liquide_totaal = liquide_spaargeld + liquide_beleggingen
        box3_grondslag = box3_liquide_grondslag + box3_vaste_grondslag
        if liquide_totaal > Decimal("0") or box3_grondslag > Decimal("0"):
            spaargeld_fractie = self.bereken_spaargeld_fractie_startvermogen(peildatum)
            return {
                "bron": "vermogensitems",
                "liquide_startvermogen": liquide_totaal,
                "box3_grondslag": box3_grondslag,
                "box3_liquide_grondslag": box3_liquide_grondslag,
                "box3_vaste_grondslag": box3_vaste_grondslag,
                "box3_spaargeld_fractie": spaargeld_fractie,
            }

        spaargeld_legacy = self.spaargeld_start
        beleggingen_legacy = self.beleggingen_start
        legacy_totaal = spaargeld_legacy + beleggingen_legacy
        return {
            "bron": "legacy",
            "liquide_startvermogen": legacy_totaal,
            "box3_grondslag": legacy_totaal,
            "box3_liquide_grondslag": legacy_totaal,
            "box3_vaste_grondslag": Decimal("0"),
            "box3_spaargeld_fractie": self.bereken_spaargeld_fractie_startvermogen(peildatum),
        }
    
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
        
        # Als er geen componenten zijn, gebruik een default van 50/50
        if totaal == Decimal("0"):
            # Fallback: gebruik oude box3_spaargeld_fractie indien beschikbaar
            if self.box3_spaargeld_fractie is not None:
                return self.box3_spaargeld_fractie
            return Decimal("0.5")  # Default 50/50 split
        
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
            if item.type in (VermogensType.EIGEN_WONING, VermogensType.HYPOTHEEK):
                continue
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

    def verzamel_eigen_woning_invoer_uit_vermogensitems(self, jaar: int | None = None) -> dict[str, Any]:
        """Verzamel fiscale eigen-woninginvoer uit vermogensitems.

        Retourneert de ruwe bronwaarden die uit Vermogen & Bezittingen zijn afgeleid,
        zodat zowel opslag/uitlezing als accountantberekening dezelfde bron gebruiken.
        """
        eigen_woning_items = [item for item in self.vermogensitems if item.type == VermogensType.EIGEN_WONING]
        hypotheek_items = [item for item in self.vermogensitems if item.type == VermogensType.HYPOTHEEK]

        peildatum = date(jaar, 1, 1) if jaar is not None else date.today()
        jaar_start = date(jaar, 1, 1) if jaar is not None else peildatum
        jaar_einde = date(jaar, 12, 31) if jaar is not None else peildatum

        def is_relevant_voor_jaar(item: VermogensItem) -> bool:
            if item.aanschafdatum and item.aanschafdatum > jaar_einde:
                return False
            if item.verkoopdatum and item.verkoopdatum < jaar_start:
                return False
            return True

        relevante_woningen = [item for item in eigen_woning_items if is_relevant_voor_jaar(item)]
        relevante_hypotheken = [item for item in hypotheek_items if is_relevant_voor_jaar(item)]

        woz_waarde = sum(
            (item.waarde_op_datum(peildatum) if item.saldostanden else
             item.woz_waarde if item.woz_waarde is not None else item.aanschafwaarde)
            for item in relevante_woningen
        )
        betaalde_hypotheekrente = sum(
            item.aanschafwaarde * (item.hypotheekrente_pct or Decimal("0")) / Decimal("100")
            for item in relevante_hypotheken
            if item.is_primaire_woning
            and (item.einddatum_aftrekbaarheid is None or item.einddatum_aftrekbaarheid >= jaar_start)
        )
        eigenwoningschuld_begin = sum(
            item.aanschafwaarde
            for item in relevante_hypotheken
            if item.is_primaire_woning
        )

        return {
            "heeft_invoer": bool(relevante_woningen or relevante_hypotheken),
            "woning_items": relevante_woningen,
            "hypotheek_items": relevante_hypotheken,
            "woz_waarde": woz_waarde,
            "betaalde_hypotheekrente": betaalde_hypotheekrente,
            "eigenwoningschuld_begin": eigenwoningschuld_begin,
            "eigenwoningschuld_eind": eigenwoningschuld_begin,
        }

    def sync_eigen_woning_uit_vermogensitems(self, jaar: int | None = None) -> EigenWoningData:
        """Synchroniseer het legacy read model vanuit vermogensitems.

        De vermogensitems zijn de fiscale bron. ``Scenario.eigen_woning`` blijft
        alleen beschikbaar voor backward compatibility met opgeslagen scenario's.
        """
        invoer = self.verzamel_eigen_woning_invoer_uit_vermogensitems(jaar)
        if not invoer["heeft_invoer"]:
            return self.eigen_woning

        self.heeft_eigen_woning = bool(invoer["heeft_invoer"] or self.heeft_eigen_woning)
        self.eigen_woning = EigenWoningData(
            woz_waarde=invoer["woz_waarde"],
            betaalde_hypotheekrente=invoer["betaalde_hypotheekrente"],
            overige_aftrekbare_kosten=self.eigen_woning.overige_aftrekbare_kosten,
            eigenwoningschuld_begin=invoer["eigenwoningschuld_begin"],
            eigenwoningschuld_eind=invoer["eigenwoningschuld_eind"],
        )
        return self.eigen_woning

    def verzamel_fiscale_eigen_woning_invoer(
        self,
        jaar: int | None = None,
        heeft_partner: bool = False,
    ) -> dict[str, Any]:
        """Verzamel fiscale eigen-woninginvoer voor huishouden en per persoon.

        Vermogensitems zijn de primaire bron. Alleen als daar geen relevante
        invoer aanwezig is, valt deze helper terug op de legacy scenario-invoer.
        Huishoudinvoer wordt bij partners altijd 50/50 verdeeld.
        """

        invoer = self.verzamel_eigen_woning_invoer_uit_vermogensitems(jaar)
        heeft_vermogensinvoer = bool(invoer["heeft_invoer"])

        if heeft_vermogensinvoer:
            huishouden = EigenWoningData(
                woz_waarde=invoer["woz_waarde"],
                betaalde_hypotheekrente=invoer["betaalde_hypotheekrente"],
                overige_aftrekbare_kosten=self.eigen_woning.overige_aftrekbare_kosten,
                eigenwoningschuld_begin=invoer["eigenwoningschuld_begin"],
                eigenwoningschuld_eind=invoer["eigenwoningschuld_eind"],
            )
            bron = "vermogensitems"
        else:
            heeft_legacy_invoer = self.heeft_eigen_woning or any(
                waarde != Decimal("0")
                for waarde in (
                    self.eigen_woning.woz_waarde,
                    self.eigen_woning.betaalde_hypotheekrente,
                    self.eigen_woning.overige_aftrekbare_kosten,
                    self.eigen_woning.eigenwoningschuld_begin,
                    self.eigen_woning.eigenwoningschuld_eind,
                )
            )
            if not heeft_legacy_invoer:
                return {
                    "heeft_invoer": False,
                    "bron": "geen",
                    "huishouden": EigenWoningData(),
                    "p1": EigenWoningData(),
                    "p2": None,
                    "woning_items": [],
                    "hypotheek_items": [],
                }
            huishouden = self.eigen_woning.model_copy(deep=True)
            bron = "scenario"

        factor = Decimal("0.5") if heeft_partner else Decimal("1")
        p1 = EigenWoningData(
            woz_waarde=huishouden.woz_waarde * factor,
            betaalde_hypotheekrente=huishouden.betaalde_hypotheekrente * factor,
            overige_aftrekbare_kosten=huishouden.overige_aftrekbare_kosten * factor,
            eigenwoningschuld_begin=huishouden.eigenwoningschuld_begin * factor,
            eigenwoningschuld_eind=huishouden.eigenwoningschuld_eind * factor,
        )
        p2 = None
        if heeft_partner:
            p2 = EigenWoningData(
                woz_waarde=huishouden.woz_waarde * factor,
                betaalde_hypotheekrente=huishouden.betaalde_hypotheekrente * factor,
                overige_aftrekbare_kosten=huishouden.overige_aftrekbare_kosten * factor,
                eigenwoningschuld_begin=huishouden.eigenwoningschuld_begin * factor,
                eigenwoningschuld_eind=huishouden.eigenwoningschuld_eind * factor,
            )

        return {
            "heeft_invoer": True,
            "bron": bron,
            "huishouden": huishouden,
            "p1": p1,
            "p2": p2,
            "woning_items": invoer["woning_items"] if heeft_vermogensinvoer else [],
            "hypotheek_items": invoer["hypotheek_items"] if heeft_vermogensinvoer else [],
        }

    # --- Inheritance helpers ---
    
    def is_base_scenario(self) -> bool:
        """Check of dit een base scenario is (geen parent)."""
        return self.parent_naam is None

    def is_derived_scenario(self) -> bool:
        """Check of dit een afgeleid scenario is (heeft parent)."""
        return self.parent_naam is not None

    def is_override(self, field_path: str) -> bool:
        """
        Check of een veld een override is in dit scenario.
        
        Args:
            field_path: Dotted path naar veld, bijv. "rendement_pct".
        
        Returns:
            True als het veld een override is in dit scenario.
        """
        return field_path in self.overrides

    def get_override_count(self) -> int:
        """Aantal overrides in dit scenario."""
        return len(self.overrides)

    def set_override(self, field_path: str, value: Any) -> None:
        """
        Stel een override in voor een veld.
        
        Args:
            field_path: Dotted path naar veld.
            value: De nieuwe waarde.
        """
        self.overrides[field_path] = value
        self.laatst_gewijzigd_op = datetime.now()

    def remove_override(self, field_path: str) -> None:
        """
        Verwijder een override (valt terug op parent waarde).
        
        Args:
            field_path: Dotted path naar veld.
        """
        self.overrides.pop(field_path, None)
        self.laatst_gewijzigd_op = datetime.now()
