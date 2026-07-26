import assert from "node:assert/strict";
import test from "node:test";

import {
  analyzeMpoRows,
  normalizeMpoDate,
  normalizeMpoRow,
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
