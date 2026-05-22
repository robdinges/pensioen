"""Vermogensitem: een bezit met waarde, waardering en box 3 behandeling."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_validator, model_validator


class VermogensType(str, Enum):
    """Type vermogensitem met specifieke waarderingsregels."""

    SPAARGELD = "spaargeld"              # spaarrekening met rente
    BELEGGINGEN = "beleggingen"          # beleggingsportefeuille met rendement
    EIGEN_WONING = "eigen_woning"        # eigen woning (box 1 eigenwoningforfait, niet box 3)
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
    """

    omschrijving: str
    type: VermogensType
    persoon: str = "Huishouden"  # "P1", "P2" of "Huishouden"
    
    # Waarde en waardering
    aanschafwaarde: Decimal              # beginwaarde of aankoopprijs
    aanschafdatum: date | None = None    # datum aankoop (None = bij start planning)
    groei_pct: Decimal = Decimal("0")    # jaarlijkse groei (+) of afschrijving (-)
    
    # Verkoop (optioneel)
    verkoopdatum: date | None = None     # datum verkoop (None = behouden)
    verkoopprijs: Decimal | None = None  # opbrengst verkoop (None = actuele waarde)
    
    # Box 3 belasting
    box3_belast: bool = True             # wel/niet box 3 heffing
    
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
    def valideer_box3_vrijstellingen(self) -> VermogensItem:
        """Zet box3_belast automatisch op False voor vrijgestelde types."""
        if self.type == VermogensType.EIGEN_WONING:
            # Eigen woning valt sinds 2026 niet meer onder box 3 (eigenwoningforfait box 1)
            self.box3_belast = False
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
