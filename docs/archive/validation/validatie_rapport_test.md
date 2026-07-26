# Belastingvergelijking: dutch_tax vs pensioen-app

> Historisch validatierapport uit 2026-05-25; niet gebruiken als actuele
> teststatus.

**Huishouden**: TestCase_Alleenstaand_Simpel
**Submission jaar**: 2025
**Berekening jaar**: 2026
**Gegenereerd**: 2026-05-25 16:07:24

---

## 📊 Samenvatting

- **Totaal verschillen**: 1
  - Kritiek: 0
  - Significant: 1

- **Pensioen-app totaal**: €0.00 **bij te betalen**

### Conclusies

- Gevonden: 1 verschillen (0 kritiek, 1 significant)
- ℹ️ Tariefverschil: dutch_tax 2025 vs pensioen-app 2026 - kleine verschillen in heffingskortingen/schijven zijn normaal
- ℹ️ Heffingskortingen verschillen: dutch_tax gebruikt 'algemene korting', pensioen-app berekent AHK/arbeidskorting/ouderenkorting apart

### 🎯 Aanbevelingen voor Pensioen-app

1. VERIFICATIE: Controleer of pensioen-app heffingskortingen formules up-to-date zijn voor 2026

---

## 🔍 Gedetailleerde Verschillenanalyse

### Heffingskortingen - Jan Testpersoon

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Totale heffingskorting | €4,801.00 | €5,246.00 | +€445.00 | +9.3% | 🟡 SIGNIFICANT | Tariefverschil 2025→2026 én berekeningsverschil (dutch_tax: algemene korting, pensioen-app: AHK+arbeidskorting+ouderen) |

---

## 💰 Pensioen-app Berekening Details

### Jan Testpersoon (T001)

**Box 1**

- Bruto inkomen: €18,500.00
- Waarvan arbeidsinkomen: €0.00
- Belasting voor kortingen: €3,302.25

**Heffingskortingen**

- Algemene heffingskorting: €3,362.00
- Arbeidskorting: €0.00
- Ouderenkorting: €1,884.00
- **Totaal**: €5,246.00

- Netto belasting Box 1: €0.00
- Box 3 aandeel: €119.05
- **Totale belasting**: €0.00

- Vooraf betaald: €0.00
- **Te betalen**: €0.00

### Box 3 (Huishouden)

- Totaal vermogen: €70,000.00
- Vrijstelling: €59,357.00
- Belastbaar vermogen: €10,643.00
- Spaargeld fractie: 64.3%
- **Totale Box 3 heffing**: €119.05

---

## ℹ️ Metadata

- Belastingconfig gebruikt: 2026 (exact)
- Heeft fiscaal partner: False
- Aantal kinderen: 0

---

## ⚠️ Disclaimer

Dit is een **validatie tool** die dutch_tax (2025 submission) vergelijkt met pensioen-app berekening (2026 tarieven). Verschillen kunnen veroorzaakt worden door:

1. Tariefjaar verschil (2025 vs 2026)
2. Ontbrekende features in pensioen-app (eigenwoningforfait, aftrekposten)
3. Andere berekeningssystematiek (heffingskortingen, Box 3 forfaits)
4. Data mapping issues

**Deze tool is NIET bedoeld voor productiegebruik** — alleen voor interne validatie.
