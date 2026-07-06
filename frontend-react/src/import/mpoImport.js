const MPO_KOLOM_MAP = {
  uitvoerder: "uitvoerder",
  regeling: "regeling",
  type_pensioen: "type_pensioen",
  type: "type_pensioen",
  ingangsdatum: "ingangsdatum",
  einddatum: "einddatum",
  bruto_per_jaar: "bruto_per_jaar",
  "bruto per jaar": "bruto_per_jaar",
  "bruto jaarbedrag": "bruto_per_jaar",
  indexatie_verwacht_pct: "indexatie_verwacht_pct",
  "indexatie verwacht %": "indexatie_verwacht_pct",
};

function normalizeHeader(value) {
  return String(value || "").trim().toLowerCase();
}

export function normalizeMpoRow(rawRow) {
  const mapped = {};
  Object.entries(rawRow || {}).forEach(([key, val]) => {
    const normalizedKey = normalizeHeader(key);
    const mappedKey = MPO_KOLOM_MAP[normalizedKey] || normalizedKey;
    mapped[mappedKey] = val;
  });
  return mapped;
}

function parseDecimalText(value) {
  if (value === null || value === undefined) {
    return 0;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0;
  }
  const cleaned = String(value).replace(/\./g, "").replace(",", ".").trim();
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : 0;
}

function parseIsoDate(value) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDateToIso(value) {
  if (!(value instanceof Date) || Number.isNaN(value.getTime())) {
    return "";
  }

  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function leeftijdBlokNaarIso(blok, geboortedatum) {
  const leeftijd = blok?.Leeftijd;
  const geboorte = parseIsoDate(geboortedatum);
  if (!leeftijd || !geboorte) {
    return "";
  }

  const jaren = Number(leeftijd.Jaren || 0);
  const maanden = Number(leeftijd.Maanden || 0);
  if (!Number.isFinite(jaren) || !Number.isFinite(maanden)) {
    return "";
  }

  return formatDateToIso(new Date(geboorte.getFullYear() + jaren, geboorte.getMonth() + maanden, 1));
}

function normalizeStructuredMpoJson(parsed, options = {}) {
  const ouderdomsTijdvakken = parsed?.Details?.OuderdomsPensioenDetails?.OuderdomsPensioen;
  if (!Array.isArray(ouderdomsTijdvakken) || ouderdomsTijdvakken.length === 0) {
    return [];
  }

  const sortedTijdvakken = [...ouderdomsTijdvakken].sort((left, right) => {
    const leftLeeftijd = left?.Van?.Leeftijd || {};
    const rightLeeftijd = right?.Van?.Leeftijd || {};
    const jaarDelta = Number(leftLeeftijd.Jaren || 999) - Number(rightLeeftijd.Jaren || 999);
    if (jaarDelta !== 0) {
      return jaarDelta;
    }
    return Number(leftLeeftijd.Maanden || 0) - Number(rightLeeftijd.Maanden || 0);
  });

  const pensioenMap = new Map();

  sortedTijdvakken.forEach((tijdvak) => {
    const ingangsdatum = leeftijdBlokNaarIso(tijdvak?.Van, options.geboortedatum);
    const einddatum = tijdvak?.Tot?.Leeftijd
      ? leeftijdBlokNaarIso(tijdvak.Tot, options.geboortedatum)
      : "";

    ["Pensioen", "IndicatiefPensioen"].forEach((typeSleutel) => {
      const items = Array.isArray(tijdvak?.[typeSleutel]) ? tijdvak[typeSleutel] : [];
      items.forEach((item) => {
        const herkenningsNummer = String(item?.HerkenningsNummer || "").trim();
        const uitvoerder = String(item?.PensioenUitvoerder || "").trim();
        const sleutel = `${herkenningsNummer || uitvoerder || "onbekend"}|${typeSleutel}`;
        const bestaande = pensioenMap.get(sleutel);
        const volgende = {
          herkenningsNummer,
          uitvoerder,
          typeSleutel,
          item,
          ingangsdatum: bestaande?.ingangsdatum || ingangsdatum,
          einddatum,
        };
        pensioenMap.set(sleutel, volgende);
      });
    });
  });

  return [...pensioenMap.values()].map((entry) =>
    normalizeMpoRow({
      uitvoerder: entry.uitvoerder,
      regeling: entry.herkenningsNummer || entry.uitvoerder || "MPO regeling",
      type_pensioen:
        entry.typeSleutel === "IndicatiefPensioen" ? "ouderdomspensioen indicatief" : "ouderdomspensioen",
      ingangsdatum: entry.ingangsdatum,
      einddatum: entry.einddatum,
      bruto_per_jaar: entry.item?.TeBereiken ?? entry.item?.Opgebouwd ?? 0,
      indexatie_verwacht_pct: 0,
    }),
  );
}

export function parseCsvText(csvText) {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const delimiter = lines[0].includes(";") ? ";" : ",";
  const headers = lines[0].split(delimiter).map((h) => h.trim().replace(/^"|"$/g, ""));

  return lines.slice(1).map((line) => {
    const cols = line.split(delimiter).map((col) => col.trim().replace(/^"|"$/g, ""));
    const row = {};
    headers.forEach((h, idx) => {
      row[h] = cols[idx] ?? "";
    });
    return normalizeMpoRow(row);
  });
}

export function parseJsonText(jsonText, options = {}) {
  const parsed = JSON.parse(jsonText);
  if (Array.isArray(parsed)) {
    return parsed.map((row) => normalizeMpoRow(row));
  }

  if (Array.isArray(parsed?.records)) {
    return parsed.records.map((row) => normalizeMpoRow(row));
  }

  const structuredRows = normalizeStructuredMpoJson(parsed, options);
  if (structuredRows.length > 0) {
    return structuredRows;
  }

  return [];
}

async function readJsonResponse(response) {
  const raw = await response.text();
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return { message: raw };
  }
}

export async function parsePdfViaApi(file, apiBase) {
  if (file.size === 0) {
    throw new Error("Het geselecteerde PDF-bestand is leeg.");
  }

  const formData = new FormData();
  formData.append("bestand", file);

  const response = await fetch(`${apiBase}/import/mpo/pdf`, {
    method: "POST",
    body: formData,
  });

  const data = await readJsonResponse(response);
  if (!response.ok) {
    const detail = data?.detail;
    if (typeof detail === "string") {
      throw new Error(detail);
    }
    if (detail?.message) {
      throw new Error(detail.message);
    }
    if (data?.message) {
      throw new Error(data.message);
    }
    throw new Error(`PDF-import mislukt (${response.status})`);
  }

  return Array.isArray(data?.records) ? data.records.map((row) => normalizeMpoRow(row)) : [];
}

export async function parseExcelBuffer(buffer) {
  const XLSX = await import("xlsx");
  const workbook = XLSX.read(buffer, { type: "array" });
  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) {
    return [];
  }

  const worksheet = workbook.Sheets[firstSheetName];
  const rows = XLSX.utils.sheet_to_json(worksheet, { defval: "" });
  return rows.map((row) => normalizeMpoRow(row));
}

export function rowsToPreview(rows) {
  return rows.slice(0, 8).map((row) => ({
    uitvoerder: String(row.uitvoerder || "").trim(),
    regeling: String(row.regeling || "").trim(),
    type: String(row.type_pensioen || "").trim(),
    ingangsdatum: String(row.ingangsdatum || "").trim(),
    bruto_per_jaar: String(row.bruto_per_jaar || "").trim(),
  }));
}

export function analyzeMpoRows(rows, persoonCode, createPensioenPost) {
  const posts = [];
  const warnings = [];
  const duplicateRegelingCounter = new Map();
  const seenPostKeys = new Set();

  let skippedType = 0;
  let skippedAmount = 0;
  let skippedDuplicate = 0;

  rows.forEach((row) => {
    const regelingNormalized = normalizeHeader(row.regeling || "onbekende regeling");
    duplicateRegelingCounter.set(
      regelingNormalized,
      (duplicateRegelingCounter.get(regelingNormalized) || 0) + 1,
    );

    const type = String(row.type_pensioen || "ouderdoms").toLowerCase();
    const isRelevant =
      type.includes("ouderdom") ||
      type.includes("ouderdoms") ||
      type.includes("pensioen") ||
      type === "";
    if (!isRelevant) {
      skippedType += 1;
      return;
    }

    const uitvoerder = String(row.uitvoerder || "").trim();
    const regeling = String(row.regeling || "").trim();
    const title = [uitvoerder, regeling].filter(Boolean).join(" - ") || "MPO pensioen";

    const bedrag = parseDecimalText(row.bruto_per_jaar);
    if (bedrag <= 0) {
      skippedAmount += 1;
      return;
    }

    const dedupeKey = [
      persoonCode,
      normalizeHeader(uitvoerder),
      normalizeHeader(regeling),
      String(row.ingangsdatum || "").trim(),
      String(bedrag),
    ].join("|");
    if (seenPostKeys.has(dedupeKey)) {
      skippedDuplicate += 1;
      return;
    }
    seenPostKeys.add(dedupeKey);

    const indexatie = parseDecimalText(row.indexatie_verwacht_pct);
    posts.push(
      createPensioenPost({
        persoonCode,
        title,
        bedrag,
        ingangsdatum: row.ingangsdatum ? String(row.ingangsdatum) : "",
        einddatum: row.einddatum ? String(row.einddatum) : "",
        indexatie,
      }),
    );
  });

  const duplicateRegelingen = [...duplicateRegelingCounter.entries()]
    .filter(([, count]) => count > 1)
    .map(([regeling, count]) => `${regeling} (${count}x)`)
    .slice(0, 8);

  if (duplicateRegelingen.length > 0) {
    warnings.push(
      `Mogelijke duplicaten gevonden op regeling: ${duplicateRegelingen.join(", ")}`,
    );
  }

  if (skippedType > 0) {
    warnings.push(`${skippedType} regel(s) overgeslagen wegens niet-ondersteund pensioentype.`);
  }
  if (skippedAmount > 0) {
    warnings.push(`${skippedAmount} regel(s) overgeslagen wegens leeg of ongeldig jaarbedrag.`);
  }
  if (skippedDuplicate > 0) {
    warnings.push(`${skippedDuplicate} exacte duplicate regel(s) overgeslagen.`);
  }

  return {
    posts,
    warnings,
    stats: {
      bronregels: rows.length,
      geimporteerd: posts.length,
      overgeslagenType: skippedType,
      overgeslagenBedrag: skippedAmount,
      overgeslagenDuplicaat: skippedDuplicate,
    },
  };
}