import assert from "node:assert/strict";
import test from "node:test";

import {
  analyzeMpoRows,
  normalizeMpoDate,
  normalizeMpoRow,
  parseJsonText,
  rowsToPreview,
} from "../src/import/mpoImport.js";

test("normaliseert gangbare MPO-datumnotaties naar ISO", () => {
  assert.equal(normalizeMpoDate("01-04-2035"), "2035-04-01");
  assert.equal(normalizeMpoDate("1/4/2035"), "2035-04-01");
  assert.equal(normalizeMpoDate("2035-04-01T00:00:00"), "2035-04-01");
  assert.equal(normalizeMpoDate("20350401"), "2035-04-01");
});

test("normaliseert een Excel-datumserienummer naar ISO", () => {
  assert.equal(normalizeMpoDate(49400), "2035-04-01");
});

test("gebruikt de genormaliseerde ingangsdatum in preview en pensioencomponent", () => {
  const row = normalizeMpoRow({
    Uitvoerder: "Testfonds",
    Regeling: "Ouderdomspensioen",
    Type: "ouderdoms",
    Ingangsdatum: "01-04-2035",
    bruto_per_jaar: "12000",
  });

  assert.equal(rowsToPreview([row])[0].ingangsdatum, "2035-04-01");

  const result = analyzeMpoRows([row], "P1", (values) => values);
  assert.equal(result.posts.length, 1);
  assert.equal(result.posts[0].ingangsdatum, "2035-04-01");
});

test("kiest bij historische en toekomstige tijdvakken de toekomstige pensioenstart", () => {
  const pensioen = {
    TeBereiken: 12000,
    Opgebouwd: 8000,
    PensioenUitvoerder: "Testfonds",
    HerkenningsNummer: "REG-1",
    StandPer: "2026-03-01",
  };
  const rows = parseJsonText(JSON.stringify({
    TijdstipAanmakenBericht: "2026-03-02T10:00:00+01:00",
    Details: {
      OuderdomsPensioenDetails: {
        OuderdomsPensioen: [
          {
            Van: { Leeftijd: { Jaren: 47, Maanden: 0 } },
            Tot: { Leeftijd: { Jaren: 68, Maanden: 0 } },
            Pensioen: [pensioen],
          },
          {
            Van: { Leeftijd: { Jaren: 68, Maanden: 0 } },
            Tot: { OuderdomsPensioenEvent: "Overlijden" },
            Pensioen: [pensioen],
          },
        ],
      },
    },
  }), { geboortedatum: "1960-03-15" });

  assert.equal(rows.length, 1);
  assert.equal(rows[0].ingangsdatum, "2028-03-01");
});

test("gebruikt bij één doorlopend tijdvak het toekomstige Tot-moment", () => {
  const rows = parseJsonText(JSON.stringify({
    Details: {
      OuderdomsPensioenDetails: {
        OuderdomsPensioen: [{
          Van: { Leeftijd: { Jaren: 47, Maanden: 0 } },
          Tot: { Leeftijd: { Jaren: 68, Maanden: 0 } },
          Pensioen: [{
            TeBereiken: 12000,
            PensioenUitvoerder: "Testfonds",
            HerkenningsNummer: "REG-ENKEL",
            StandPer: "2026-03-01",
          }],
        }],
      },
    },
  }), { geboortedatum: "1960-03-15" });

  assert.equal(rows[0].ingangsdatum, "2028-03-01");
});

test("geeft expliciete vanafDatum in pensioenitem voorrang op historisch tijdvak", () => {
  const rows = parseJsonText(JSON.stringify({
    Details: {
      OuderdomsPensioenDetails: {
        OuderdomsPensioen: [{
          Van: { Leeftijd: { Jaren: 47, Maanden: 0 } },
          Tot: { OuderdomsPensioenEvent: "Overlijden" },
          Pensioen: [{
            TeBereiken: 12000,
            PensioenUitvoerder: "Testfonds",
            HerkenningsNummer: "REG-EXPLICIET",
            StandPer: "01-03-2026",
            vanafDatum: "19-04-2040",
            vanafLeeftijdJaren: 68,
            vanafLeeftijdMaanden: 0,
            totOverlijden: true,
          }],
        }],
      },
    },
  }), { geboortedatum: "1972-04-19" });

  assert.equal(rows[0].ingangsdatum, "2040-04-19");
  assert.equal(rows[0].einddatum, "");
});
