# API- en sessiedeprecatiebeleid

Status: goedgekeurd door de producteigenaar op 26 juli 2026.

- API v1 en outputcontract `1.0` blijven backward compatible.
- Additieve optionele velden zijn toegestaan binnen v1.
- Verwijderen, hernoemen of betekenis wijzigen vereist API v2.
- Een deprecated veld krijgt eerst een vervangend veld, waarschuwing en
  migratiebeschrijving.
- Oude React-sessies blijven leesbaar; migratie vindt tijdens hydratatie plaats.
- Verwijdering volgt pas nadat fixtures, sessietests en beide frontends geen
  caller meer hebben.
- Security- of datacorruptieproblemen mogen versneld worden beëindigd, met een
  expliciete breaking-change-notitie.
