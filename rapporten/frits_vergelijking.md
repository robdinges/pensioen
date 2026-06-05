# Belastingvergelijking: dutch_tax vs pensioen-app

**Huishouden**: Frits
**Submission jaar**: 2025
**Berekening jaar**: 2026
**Gegenereerd**: 2026-05-25 16:12:37

---

## 📊 Samenvatting

- **Totaal verschillen**: 3
  - Kritiek: 0
  - Significant: 2

- **Pensioen-app totaal**: €4,569.80 **bij te betalen**

### Conclusies

- Gevonden: 3 verschillen (0 kritiek, 2 significant)
- ⚠️ Aftrekposten aanwezig in dutch_tax, ontbreken in pensioen-app
- ℹ️ Dividend ingehouden: €24.00
- ℹ️ Tariefverschil: dutch_tax 2025 vs pensioen-app 2026 - kleine verschillen in heffingskortingen/schijven zijn normaal
- ℹ️ Heffingskortingen verschillen: dutch_tax gebruikt 'algemene korting', pensioen-app berekent AHK/arbeidskorting/ouderenkorting apart

### 🎯 Aanbevelingen voor Pensioen-app

1. PRIORITEIT 2: Voeg ondersteuning toe voor veelvoorkomende aftrekposten (beddengoed, giften, etc.)
2. PRIORITEIT 3: Controleer of dividend ingehouden correct wordt verrekend in Box 3 berekening
3. VERIFICATIE: Controleer of pensioen-app heffingskortingen formules up-to-date zijn voor 2026

---

## 🔍 Gedetailleerde Verschillenanalyse

### Box 1 - Frits

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Aftrekposten (ONTBREKEN) | €126.00 | €0.00 | -€126.00 | -100.0% | 🟡 SIGNIFICANT | Pensioen-app ondersteunt geen aftrekposten. 1 aftrekpost(en) totaal €360 → belastingvoordeel ~€126 (indicatief) |

### Heffingskortingen - Frits

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Totale heffingskorting | €4,102.00 | €3,362.00 | -€740.00 | -18.0% | 🟡 SIGNIFICANT | Tariefverschil 2025→2026 én berekeningsverschil (dutch_tax: algemene korting, pensioen-app: AHK+arbeidskorting+ouderen) |

### Totaal

| Onderdeel | dutch_tax | pensioen-app | Verschil | % | Ernst | Hypothese |
|-----------|-----------|--------------|----------|---|-------|-----------|
| Vooraf betaald (loonheffing + dividend) | €24.00 | €0.00 | -€24.00 | -100.0% | 🔵 KLEIN | Pensioen-app neemt mogelijk geen dividend ingehouden mee in vooraf betaald (dutch_tax: €24.00 dividend) |

---

## 💰 Pensioen-app Berekening Details

### Frits (000000001)

**Box 1**

- Bruto inkomen: €20,192.00
- Waarvan arbeidsinkomen: €0.00
- Belasting voor kortingen: €7,218.64

**Heffingskortingen**

- Algemene heffingskorting: €3,362.00
- Arbeidskorting: €0.00
- Ouderenkorting: €0.00
- **Totaal**: €3,362.00

- Netto belasting Box 1: €3,856.64
- Box 3 aandeel: €713.16
- **Totale belasting**: €4,569.80

- Vooraf betaald: €0.00
- **Te betalen**: €4,569.80

**Aannames**

- ⚠️ Frits: 1 aftrekpost(en) (totaal €360.00) NIET meegenomen (niet ondersteund)

### Box 3 (Huishouden)

- Totaal vermogen: €118,170.00
- Vrijstelling: €59,357.00
- Belastbaar vermogen: €58,813.00
- Spaargeld fractie: 58.5%
- **Totale Box 3 heffing**: €713.16

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
