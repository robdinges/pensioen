"""Vermogensitem: een bezit met waarde, waardering en box 3 behandeling."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class VermogensType(str, Enum):
    """Type vermogensitem met specifieke waarderingsregels."""

    SPAARGELD = "spaargeld"              # spaarrekening met rente
    BELEGGINGEN = "beleggingen"          # beleggingsportefeuille met rendement
    EIGEN_WONING = "eigen_woning"        # eigen woning (box 1 eigenwoningforfait, niet box 3)
    HYPOTHEEK = "hypotheek"              # hypotheekschuld (fiscale invoer box 1; niet in vermogenstotaal)
    AUTO = "auto"                        # auto met afschrijving
    KUNST = "kunst"                      # kunst met waardestijging
    BOOT = "boot"                        # boot met afschrijving
    OVERIG = "overig"                    # overige bezittingen


class VermogensItem(BaseModel):
    """
    Een vermogensitem met aanschafwaarde, waardering en fiscale behandeling.
    
    Voor spaargeld en beleggingen: 
    - aanschafwaarde = beginsaldo
    - groei_pct = verwacht jaarlijks rendement
    - verkoopdatum = niet van toepassing
    
    Voor fysieke bezittingen (auto, kunst, boot):
    - aanschafwaarde = aankoopprijs
    - groei_pct = waardestijging (+) of afschrijving (-)
    - verkoopdatum = moment van verkoop (optioneel)
    - verkoopprijs = opbrengst bij verkoop (optioneel)
    
    Voor eigen woning (type=EIGEN_WONING):
    - aanschafwaarde = WOZ-waarde (wordt genegeerd bij berekening; gebruik woz_waarde ipv)
    - woz_waarde = WOZ-waarde per 1 januari van het belastingjaar
    - groei_pct = jaarlijkse waardestijging (default 2%)
    - box3_belast = altijd False (eigen woning niet in box 3)
    
    Voor hypotheek (type=HYPOTHEEK):
    - aanschafwaarde = Resterende schuld per 1 januari
    - groei_pct = jaarlijkse afname van schuld (aflossing; default 0)
    - is_primaire_woning = True voor primaire woning (renteaftrek box 1)
    - hypotheekrente_pct = jaarlijkse rentevoet (bijv. 2.5)
    - einddatum_aftrekbaarheid = Datum waarna rente niet meer aftrekbaar (Wet eigen woning)
    - box3_belast = altijd False (hypotheekschuld niet in box 3)
    """

    omschrijving: str
    type: VermogensType
    persoon: str = "Huishouden"  # "P1", "P2" of "Huishouden"
    
    # Waarde en waardering
    aanschafwaarde: Decimal              # beginwaarde of aankoopprijs
    aanschafdatum: date | None = None    # datum aankoop (None = bij start planning)
    groei_pct: Decimal = Decimal("0")    # jaarlijkse groei (+) of afschrijving (-)
    
    jaarlijkse_inleg: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    # None behoudt oude scenario-inleg; expliciet 0 schakelt die fallback uit.

    # Verkoop (optioneel)
    verkoopdatum: date | None = None     # datum verkoop (None = behouden)
    verkoopprijs: Decimal | None = None  # opbrengst verkoop (None = actuele waarde)
    
    # Box 3 belasting
    box3_belast: bool = True             # wel/niet box 3 heffing
    
    # Eigen woning specifiek (voor type=EIGEN_WONING)
    woz_waarde: Decimal | None = None    # WOZ-waarde per 1 januari
    woz_jaarlijkse_stijging_pct: Decimal = Decimal("2")  # verwachte jaarlijkse waardestijging
    
    # Hypotheek specifiek (voor type=HYPOTHEEK)
    is_primaire_woning: bool | None = None  # primaire woning (aftrekbaarheid rente)
    hypotheekrente_pct: Decimal | None = None  # jaarlijkse rente percentage
    einddatum_aftrekbaarheid: date | None = None  # einddatum renteaftrek (Wet eigen woning)
    
    @field_validator("aanschafwaarde")
    @classmethod
    def aanschafwaarde_niet_negatief(cls, v: Decimal) -> Decimal:
        if v < Decimal("0"):
            raise ValueError("aanschafwaarde mag niet negatief zijn.")
        return v
    
    @field_validator("groei_pct")
    @classmethod
    def groei_pct_realistisch(cls, v: Decimal) -> Decimal:
        if not (Decimal("-100") <= v <= Decimal("100")):
            raise ValueError("groei_pct moet tussen -100% en +100% liggen.")
        return v
    
    @field_validator("hypotheekrente_pct")
    @classmethod
    def hypotheekrente_pct_realistisch(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and not (Decimal("0") <= v <= Decimal("20")):
            raise ValueError("hypotheekrente_pct moet tussen 0% en 20% liggen.")
        return v
    
    @model_validator(mode="after")
    def valideer_verkoop(self) -> VermogensItem:
        """Valideer verkoopdatum en verkoopprijs consistentie."""
        if self.verkoopprijs is not None and self.verkoopdatum is None:
            raise ValueError("verkoopprijs vereist een verkoopdatum.")
        if self.verkoopprijs is not None and self.verkoopprijs < Decimal("0"):
            raise ValueError("verkoopprijs mag niet negatief zijn.")
        if self.aanschafdatum and self.verkoopdatum and self.verkoopdatum < self.aanschafdatum:
            raise ValueError("verkoopdatum mag niet vóór aanschafdatum liggen.")
        return self
    
    @model_validator(mode="after")
    def valideer_eigen_woning(self) -> VermogensItem:
        """Valideer eigen woning specifieke velden."""
        if self.type == VermogensType.EIGEN_WONING:
            if self.woz_waarde is None:
                self.woz_waarde = self.aanschafwaarde
            if self.woz_waarde <= Decimal("0"):
                raise ValueError("Eigen woning vereist een positieve WOZ-waarde.")
            self.box3_belast = False  # Eigenwoningforfait (box 1), niet box 3
        return self
    
    @model_validator(mode="after")
    def valideer_hypotheek(self) -> VermogensItem:
        """Valideer hypotheek specifieke velden."""
        if self.type == VermogensType.HYPOTHEEK:
            if self.is_primaire_woning is None:
                raise ValueError("Hypotheek vereist is_primaire_woning.")
            if self.hypotheekrente_pct is None or self.hypotheekrente_pct < Decimal("0"):
                raise ValueError("Hypotheek vereist positief rente percentage.")
            self.box3_belast = False  # Hypotheekschuld niet in box 3
        return self
    
    def waarde_op_datum(self, peildatum: date) -> Decimal:
        """
        Bereken de waarde van dit item op een specifieke datum.
        
        Args:
            peildatum: Datum waarop waarde wordt bepaald.
        
        Returns:
            Waarde in euro's. Decimal("0") als item nog niet gekocht of al verkocht.
        """
        # Nog niet aangekocht
        if self.aanschafdatum and peildatum < self.aanschafdatum:
            return Decimal("0")

        # Al verkocht
        if self.verkoopdatum and peildatum > self.verkoopdatum:
            return Decimal("0")

        # Eigen woning: gebruik expliciete WOZ-waarde en eigen groeiperiode
        if self.type == VermogensType.EIGEN_WONING:
            basiswaarde = self.woz_waarde if self.woz_waarde is not None else self.aanschafwaarde
            groei_pct = self.woz_jaarlijkse_stijging_pct if self.woz_jaarlijkse_stijging_pct is not None else self.groei_pct
            if groei_pct == Decimal("0"):
                return basiswaarde

            startdatum = self.aanschafdatum if self.aanschafdatum else peildatum
            jaren = Decimal(str((peildatum - startdatum).days / 365.25))
            groei_basis = Decimal("1") + groei_pct / Decimal("100")
            groei_factor = Decimal(str(float(groei_basis) ** float(jaren)))
            return basiswaarde * groei_factor

        # Hypotheek: toon als aparte fiscale invoer, niet als minpost in vermogenstotalen
        if self.type == VermogensType.HYPOTHEEK:
            schuld = self.aanschafwaarde
            if self.groei_pct == Decimal("0"):
                return schuld

            startdatum = self.aanschafdatum if self.aanschafdatum else peildatum
            jaren = Decimal(str((peildatum - startdatum).days / 365.25))
            groei_basis = Decimal("1") + self.groei_pct / Decimal("100")
            groei_factor = Decimal(str(float(groei_basis) ** float(jaren)))
            return schuld * groei_factor
        
        # Op verkoopdatum: gebruik verkoopprijs indien opgegeven
        if self.verkoopdatum and peildatum == self.verkoopdatum:
            if self.verkoopprijs is not None:
                return self.verkoopprijs
            # Geen verkoopprijs opgegeven: bereken actuele waarde
        
        # Bereken aantal jaren sinds aankoop
        startdatum = self.aanschafdatum if self.aanschafdatum else peildatum
        if peildatum < startdatum:
            return Decimal("0")
        
        jaren = Decimal(str((peildatum - startdatum).days / 365.25))
        
        # Waardeontwikkeling met groei/afschrijving
        if self.groei_pct == Decimal("0"):
            return self.aanschafwaarde
        
        # Gebruik float voor machtsverheffing, converteer terug naar Decimal
        groei_basis = Decimal("1") + self.groei_pct / Decimal("100")
        groei_factor = Decimal(str(float(groei_basis) ** float(jaren)))
        waarde = self.aanschafwaarde * groei_factor
        
        # Afschrijving kan niet onder nul uitkomen
        if waarde < Decimal("0"):
            waarde = Decimal("0")
        
        return waarde
    
    def is_actief_op(self, peildatum: date) -> bool:
        """Is dit vermogensitem actief (in bezit) op de peildatum?"""
        if self.aanschafdatum and peildatum < self.aanschafdatum:
            return False
        if self.verkoopdatum and peildatum > self.verkoopdatum:
            return False
        return True
