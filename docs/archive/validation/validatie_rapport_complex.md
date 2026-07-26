# Belastingvergelijking: dutch_tax vs pensioen-app

> Historisch validatierapport uit 2026-05-25; niet gebruiken als actuele
> teststatus.

**Huishouden**: TestCase_Partner_Complexer
**Submission jaar**: 2025
**Berekening jaar**: 2026
**Gegenereerd**: 2026-05-25 16:07:39

---

## 📊 Samenvatting

- **Totaal verschillen**: 4
  - Kritiek: 0
  - Significant: 4

- **Pensioen-app totaal**: €2,929.66 **bij te betalen**

### Conclusies

- Gevonden: 4 verschillen (0 kritiek, 4 significant)
- ⚠️ Aftrekposten aanwezig in dutch_tax, ontbreken in pensioen-app
- ℹ️ Dividend ingehouden: €125.00
- ℹ️ Tariefverschil: dutch_tax 2025 vs pensioen-app 2026 - kleine verschillen in heffingskortingen/schijven zijn normaal
- ℹ️ Heffingskortingen verschillen: dutch_tax gebruikt 'algemene korting', pensioen-app berekent AHK/arbeidskorting/ouderenkorting apart

### 🎯 Aanbevelingen voor Pensioen-app

1. PRIORITEIT 2: Voeg ondersteuning toe voor veelvoorkomende aftrekposten (beddengoed, giften, etc.)
2. PRIORITEIT 3: Controleer of dividend ingehouden correct wordt verrekend in Box 3 berekening
3. VERIFICATIE: Controleer of pensioen-app heffingskortingen formules up-to-date zijn voor 2026

---

## 🔍 Gedetailleerde Verschillenanalyse

### Box 1 - Marie Testpersoon

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Aftrekposten (ONTBREKEN) | €157.50 | €0.00 | -€157.50 | -100.0% | 🟡 SIGNIFICANT | Pensioen-app ondersteunt geen aftrekposten. 1 aftrekpost(en) totaal €450 → belastingvoordeel ~€158 (indicatief) |

### Heffingskortingen - Marie Testpersoon

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Totale heffingskorting | €3,850.00 | €4,411.78 | +€561.78 | +14.6% | 🟡 SIGNIFICANT | Tariefverschil 2025→2026 én berekeningsverschil (dutch_tax: algemene korting, pensioen-app: AHK+arbeidskorting+ouderen) |

### Heffingskortingen - Pieter Testpersoon

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Totale heffingskorting | €4,801.00 | €5,246.00 | +€445.00 | +9.3% | 🟡 SIGNIFICANT | Tariefverschil 2025→2026 én berekeningsverschil (dutch_tax: algemene korting, pensioen-app: AHK+arbeidskorting+ouderen) |

### Totaal

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Vooraf betaald (loonheffing + dividend) | €125.00 | €0.00 | -€125.00 | -100.0% | 🟡 SIGNIFICANT | Pensioen-app neemt mogelijk geen dividend ingehouden mee in vooraf betaald (dutch_tax: €125.00 dividend) |

---

## 💰 Pensioen-app Berekening Details

### Marie Testpersoon (T002)

**Box 1**

- Bruto inkomen: €38,500.00
- Waarvan arbeidsinkomen: €0.00
- Belasting voor kortingen: €6,872.25

**Heffingskortingen**

- Algemene heffingskorting: €2,527.78
- Arbeidskorting: €0.00
- Ouderenkorting: €1,884.00
- **Totaal**: €4,411.78

- Netto belasting Box 1: €2,460.47
- Box 3 aandeel: €469.20
- **Totale belasting**: €2,929.66

- Vooraf betaald: €0.00
- **Te betalen**: €2,929.66

**Aannames**

- ⚠️ Marie Testpersoon: 1 aftrekpost(en) (totaal €450.00) NIET meegenomen (niet ondersteund)

### Pieter Testpersoon (T003)

**Box 1**

- Bruto inkomen: €14,500.00
- Waarvan arbeidsinkomen: €0.00
- Belasting voor kortingen: €2,588.25

**Heffingskortingen**

- Algemene heffingskorting: €3,362.00
- Arbeidskorting: €0.00
- Ouderenkorting: €1,884.00
- **Totaal**: €5,246.00

- Netto belasting Box 1: €0.00
- Box 3 aandeel: €469.20
- **Totale belasting**: €0.00

- Vooraf betaald: €0.00
- **Te betalen**: €0.00

### Box 3 (Huishouden)

- Totaal vermogen: €185,000.00
- Vrijstelling: €118,714.00
- Belastbaar vermogen: €66,286.00
- Spaargeld fractie: 45.9%
- **Totale Box 3 heffing**: €938.39

---

## ℹ️ Metadata

- Belastingconfig gebruikt: 2026 (exact)
- Heeft fiscaal partner: True
- Aantal kinderen: 0

---

## ⚠️ Disclaimer

Dit is een **validatie tool** die dutch_tax (2025 submission) vergelijkt met pensioen-app berekening (2026 tarieven). Verschillen kunnen veroorzaakt worden door:

1. Tariefjaar verschil (2025 vs 2026)
2. Ontbrekende features in pensioen-app (eigenwoningforfait, aftrekposten)
3. Andere berekeningssystematiek (heffingskortingen, Box 3 forfaits)
4. Data mapping issues

**Deze tool is NIET bedoeld voor productiegebruik** — alleen voor interne validatie.
