export const FLOW_STEPS = [
  { id: "huishouden", label: "Huishouden" },
  { id: "personen", label: "Personen" },
  { id: "import", label: "Pensioen importeren" },
  { id: "periode", label: "Berekeningsperiode" },
  { id: "scenario", label: "Scenario's" },
  { id: "componenten", label: "Inkomen & vermogen" },
  { id: "resultaten", label: "Resultaten" },
  { id: "accountant", label: "Berekening in detail" },
  { id: "rapport", label: "Rapport" },
];

export const TYPE_CONFIG = {
  loon: {
    section: "inkomsten",
    label: "Loon",
    hint: "Periodiek arbeidsinkomen.",
    fields: ["persoon", "bedrag", "bedrag_type", "frequentie", "startdatum", "einddatum", "inflatie_pct"],
  },
  uitkering: {
    section: "inkomsten",
    label: "Uitkering",
    hint: "WW, WIA of andere periodieke uitkering.",
    fields: ["persoon", "bedrag", "bedrag_type", "frequentie", "startdatum", "einddatum", "inflatie_pct"],
  },
  pensioen: {
    section: "inkomsten",
    label: "Pensioen",
    hint: "AOW of werkgeverspensioen.",
    fields: ["persoon", "bedrag", "bedrag_type", "frequentie", "startdatum", "einddatum", "inflatie_pct"],
  },
  uitgave: {
    section: "inkomsten",
    label: "Uitgave",
    hint: "Periodieke uitgave buiten box 1 en box 3.",
    fields: ["persoon", "bedrag", "frequentie", "startdatum", "einddatum", "inflatie_pct"],
  },
  eenmalige_inkomsten: {
    section: "inkomsten",
    label: "Eenmalige inkomsten",
    hint: "Bonus, erfenis, verkoopopbrengst.",
    fields: ["persoon", "bedrag", "datum"],
  },
  eenmalige_uitgaven: {
    section: "inkomsten",
    label: "Eenmalige uitgaven",
    hint: "Verbouwing, auto, schenking.",
    fields: ["persoon", "bedrag", "datum"],
  },
  sparen: {
    section: "vermogen",
    label: "Sparen",
    hint: "Spaarrekening of deposito.",
    fields: ["persoon", "beginwaarde", "peildatum", "inleg", "groei_pct"],
  },
  beleggen: {
    section: "vermogen",
    label: "Beleggen",
    hint: "ETF, aandelen, beleggingsrekening.",
    fields: ["persoon", "beginwaarde", "peildatum", "inleg", "groei_pct"],
  },
  eigen_woning: {
    section: "vermogen",
    label: "Eigen woning",
    hint: "WOZ-waarde en verwachte waardegroei.",
    fields: ["persoon", "beginwaarde", "peildatum", "groei_pct"],
  },
  overige_bezittingen: {
    section: "vermogen",
    label: "Overige bezittingen",
    hint: "Auto, kunst, bedrijfsmiddelen, overig.",
    fields: ["persoon", "beginwaarde", "peildatum", "groei_pct"],
  },
  hypotheek: {
    section: "vermogen",
    label: "Schulden (hypotheek)",
    hint: "Hypotheekschuld met rente en aflossing.",
    fields: ["persoon", "beginwaarde", "rente_pct", "maandlast", "startdatum", "einddatum"],
  },
};

export const FIELD_META = {
  persoon: { label: "Persoon", type: "select", options: ["P1", "P2", "Huishouden"], defaultValue: "P1" },
  bedrag: { label: "Bedrag", type: "number", step: "100", defaultValue: "0" },
  bedrag_type: { label: "Bedrag type", type: "select", options: ["bruto", "netto"], defaultValue: "bruto" },
  beginwaarde: { label: "Saldo / waarde", type: "number", step: "1000", defaultValue: "0" },
  inleg: { label: "Inleg per jaar", type: "number", step: "100", defaultValue: "0" },
  maandlast: { label: "Maandlast", type: "number", step: "50", defaultValue: "0" },
  frequentie: {
    label: "Frequentie",
    type: "select",
    options: ["maandelijks", "kwartaal", "halfjaarlijks", "jaarlijks"],
    defaultValue: "maandelijks",
  },
  datum: { label: "Datum", type: "date", defaultValue: "" },
  peildatum: { label: "Peildatum saldo / waarde", type: "date", defaultValue: "" },
  startdatum: { label: "Vanaf", type: "date", defaultValue: "" },
  einddatum: { label: "T/m", type: "date", defaultValue: "" },
  groei_pct: { label: "Groei / rendement %", type: "number", step: "0.1", defaultValue: "0" },
  inflatie_pct: { label: "Inflatiecorrectie %", type: "number", step: "0.1", defaultValue: "2" },
  rente_pct: { label: "Rente %", type: "number", step: "0.1", defaultValue: "0" },
};

export const DEFAULT_API_BASE = "/api/v1";
export const OUTPUT_CONTRACT_VERSION = "1.0";
export const DEFAULT_PERSOON_NAAM = "Jan Jansen";
export const DEFAULT_GEBOORTEDATUM = "1963-03-15";

const CATEGORY_BY_TYPE = {
  loon: "arbeidsinkomen",
  uitkering: "overig_inkomen",
  pensioen: "pensioen_inkomen",
  uitgave: "uitgave",
};

const VERMOGEN_TYPE_BY_POST = {
  sparen: "spaargeld",
  beleggen: "beleggingen",
  eigen_woning: "eigen_woning",
  overige_bezittingen: "overig",
  hypotheek: "hypotheek",
};

function toAmount(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

function toIsoOrNull(value) {
  return value ? value : null;
}

export function createEmptyValues(type) {
  const fields = TYPE_CONFIG[type].fields;
  return fields.reduce((acc, field) => {
    acc[field] = FIELD_META[field].defaultValue;
    return acc;
  }, {});
}

export function euro(value) {
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value ?? 0);
}

export function decimalLike(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

export function signedEuro(value) {
  const amount = decimalLike(value);
  if (amount === 0) {
    return euro(0);
  }
  return `${amount > 0 ? "+" : "-"}${euro(Math.abs(amount))}`;
}

export function signedPercentagePoints(value) {
  const amount = decimalLike(value);
  return `${amount > 0 ? "+" : ""}${amount.toFixed(1)} pp`;
}

export function createPost(type) {
  return {
    id: crypto.randomUUID(),
    type,
    titel: TYPE_CONFIG[type].label,
    values: createEmptyValues(type),
  };
}

export function createDefaultScenarioData() {
  return {
    posts: [createPost("loon"), createPost("sparen")],
    jaarVan: String(new Date().getFullYear()),
    jaarTot: String(new Date().getFullYear() + 20),
    importBestandP1Naam: "",
    importBestandP2Naam: "",
    importPreviewP1: [],
    importPreviewP2: [],
    importWarningsP1: [],
    importWarningsP2: [],
    importStatsP1: null,
    importStatsP2: null,
    resultaat: null,
    inputSignatureAtCalculation: "",
    calculationStatus: "idle",
  };
}

export function createScenarioSnapshot(state) {
  return {
    posts: state.posts,
    jaarVan: state.jaarVan,
    jaarTot: state.jaarTot,
    importBestandP1Naam: state.importBestandP1Naam,
    importBestandP2Naam: state.importBestandP2Naam,
    importPreviewP1: state.importPreviewP1,
    importPreviewP2: state.importPreviewP2,
    importWarningsP1: state.importWarningsP1,
    importWarningsP2: state.importWarningsP2,
    importStatsP1: state.importStatsP1,
    importStatsP2: state.importStatsP2,
    resultaat: state.resultaat,
    inputSignatureAtCalculation: state.inputSignatureAtCalculation,
    calculationStatus: state.calculationStatus,
  };
}

export function createHouseholdPreferences(state = {}) {
  const defaults = createDefaultScenarioData();
  return {
    jaarVan: typeof state.jaarVan === "string" ? state.jaarVan : defaults.jaarVan,
    jaarTot: typeof state.jaarTot === "string" ? state.jaarTot : defaults.jaarTot,
    apiBase: typeof state.apiBase === "string" ? state.apiBase : DEFAULT_API_BASE,
    inkomenType: typeof state.inkomenType === "string" ? state.inkomenType : "uitkering",
    vermogenType: typeof state.vermogenType === "string" ? state.vermogenType : "beleggen",
  };
}

export function normalizeHouseholdPreferences(preferences, fallback = {}) {
  const source = preferences && typeof preferences === "object" ? preferences : {};
  return createHouseholdPreferences({ ...fallback, ...source });
}

export function normalizeScenarioSnapshot(snapshot, fallback = {}) {
  const defaults = {
    ...createDefaultScenarioData(),
    ...fallback,
  };
  const source = snapshot && typeof snapshot === "object" ? snapshot : {};

  return {
    posts: Array.isArray(source.posts) && source.posts.length > 0 ? source.posts : defaults.posts,
    jaarVan: typeof source.jaarVan === "string" ? source.jaarVan : defaults.jaarVan,
    jaarTot: typeof source.jaarTot === "string" ? source.jaarTot : defaults.jaarTot,
    importBestandP1Naam:
      typeof source.importBestandP1Naam === "string" ? source.importBestandP1Naam : defaults.importBestandP1Naam,
    importBestandP2Naam:
      typeof source.importBestandP2Naam === "string" ? source.importBestandP2Naam : defaults.importBestandP2Naam,
    importPreviewP1: Array.isArray(source.importPreviewP1) ? source.importPreviewP1 : defaults.importPreviewP1,
    importPreviewP2: Array.isArray(source.importPreviewP2) ? source.importPreviewP2 : defaults.importPreviewP2,
    importWarningsP1: Array.isArray(source.importWarningsP1) ? source.importWarningsP1 : defaults.importWarningsP1,
    importWarningsP2: Array.isArray(source.importWarningsP2) ? source.importWarningsP2 : defaults.importWarningsP2,
    importStatsP1: source.importStatsP1 && typeof source.importStatsP1 === "object" ? source.importStatsP1 : defaults.importStatsP1,
    importStatsP2: source.importStatsP2 && typeof source.importStatsP2 === "object" ? source.importStatsP2 : defaults.importStatsP2,
    resultaat: source.resultaat || defaults.resultaat,
    inputSignatureAtCalculation:
      typeof source.inputSignatureAtCalculation === "string"
        ? source.inputSignatureAtCalculation
        : defaults.inputSignatureAtCalculation,
    calculationStatus:
      typeof source.calculationStatus === "string" ? source.calculationStatus : defaults.calculationStatus,
  };
}

export function createHouseholdSnapshot(state) {
  return {
    posts: state.posts,
    apiBase: state.apiBase,
    persoonNaam: state.persoonNaam,
    geboortedatum: state.geboortedatum,
    heeftPartner: state.heeftPartner,
    partnerNaam: state.partnerNaam,
    partnerGeboortedatum: state.partnerGeboortedatum,
    scenarios: state.scenarios,
    activeScenarioId: state.activeScenarioId,
    scenarioSnapshots: state.scenarioSnapshots,
    compareScenarioId: state.compareScenarioId,
    thirdScenarioId: state.thirdScenarioId || "",
    comparisonResult: state.comparisonResult,
    importBestandP1Naam: state.importBestandP1Naam,
    importBestandP2Naam: state.importBestandP2Naam,
    importPreviewP1: state.importPreviewP1,
    importPreviewP2: state.importPreviewP2,
    importWarningsP1: state.importWarningsP1,
    importWarningsP2: state.importWarningsP2,
    importStatsP1: state.importStatsP1,
    importStatsP2: state.importStatsP2,
    jaarVan: state.jaarVan,
    jaarTot: state.jaarTot,
    resultaat: state.resultaat,
    inputSignatureAtCalculation: state.inputSignatureAtCalculation,
    calculationStatus: state.calculationStatus,
  };
}

export function createInitialHouseholdSnapshot({
  scenarioId,
  scenarioNaam = "Basisscenario",
  scenarioData = createDefaultScenarioData(),
  persoonNaam = "",
  geboortedatum = "",
} = {}) {
  const activeScenarioId = scenarioId || crypto.randomUUID();

  return createHouseholdSnapshot({
    posts: scenarioData.posts,
    apiBase: DEFAULT_API_BASE,
    persoonNaam,
    geboortedatum,
    heeftPartner: false,
    partnerNaam: "",
    partnerGeboortedatum: "",
    scenarios: [{ id: activeScenarioId, naam: scenarioNaam }],
    activeScenarioId,
    scenarioSnapshots: {
      [activeScenarioId]: scenarioData,
    },
    compareScenarioId: "",
    thirdScenarioId: "",
    comparisonResult: null,
    importBestandP1Naam: scenarioData.importBestandP1Naam,
    importBestandP2Naam: scenarioData.importBestandP2Naam,
    importPreviewP1: scenarioData.importPreviewP1,
    importPreviewP2: scenarioData.importPreviewP2,
    importWarningsP1: scenarioData.importWarningsP1,
    importWarningsP2: scenarioData.importWarningsP2,
    importStatsP1: scenarioData.importStatsP1,
    importStatsP2: scenarioData.importStatsP2,
    jaarVan: scenarioData.jaarVan,
    jaarTot: scenarioData.jaarTot,
    resultaat: scenarioData.resultaat,
    inputSignatureAtCalculation: scenarioData.inputSignatureAtCalculation,
    calculationStatus: scenarioData.calculationStatus,
  });
}

export function normalizeHouseholdSnapshot(snapshot) {
  const source = snapshot && typeof snapshot === "object" ? snapshot : {};
  const fallbackScenario = { id: crypto.randomUUID(), naam: "Basisscenario" };
  const scenarios =
    Array.isArray(source.scenarios) && source.scenarios.length > 0 ? source.scenarios : [fallbackScenario];
  const activeScenarioId =
    typeof source.activeScenarioId === "string" && scenarios.some((scenario) => scenario.id === source.activeScenarioId)
      ? source.activeScenarioId
      : scenarios[0].id;

  const fallbackScenarioData = normalizeScenarioSnapshot(source, {
    posts: Array.isArray(source.posts) && source.posts.length > 0 ? source.posts : createDefaultScenarioData().posts,
    jaarVan: typeof source.jaarVan === "string" ? source.jaarVan : createDefaultScenarioData().jaarVan,
    jaarTot: typeof source.jaarTot === "string" ? source.jaarTot : createDefaultScenarioData().jaarTot,
    importBestandP1Naam: typeof source.importBestandP1Naam === "string" ? source.importBestandP1Naam : "",
    importBestandP2Naam: typeof source.importBestandP2Naam === "string" ? source.importBestandP2Naam : "",
    importPreviewP1: Array.isArray(source.importPreviewP1) ? source.importPreviewP1 : [],
    importPreviewP2: Array.isArray(source.importPreviewP2) ? source.importPreviewP2 : [],
    importWarningsP1: Array.isArray(source.importWarningsP1) ? source.importWarningsP1 : [],
    importWarningsP2: Array.isArray(source.importWarningsP2) ? source.importWarningsP2 : [],
    importStatsP1: source.importStatsP1 && typeof source.importStatsP1 === "object" ? source.importStatsP1 : null,
    importStatsP2: source.importStatsP2 && typeof source.importStatsP2 === "object" ? source.importStatsP2 : null,
    resultaat: source.resultaat || null,
    inputSignatureAtCalculation:
      typeof source.inputSignatureAtCalculation === "string" ? source.inputSignatureAtCalculation : "",
    calculationStatus: typeof source.calculationStatus === "string" ? source.calculationStatus : "idle",
  });

  const rawScenarioSnapshots =
    source.scenarioSnapshots && typeof source.scenarioSnapshots === "object" ? source.scenarioSnapshots : {};
  const scenarioSnapshots = scenarios.reduce((acc, scenario) => {
    acc[scenario.id] = normalizeScenarioSnapshot(
      rawScenarioSnapshots[scenario.id],
      scenario.id === activeScenarioId ? fallbackScenarioData : undefined,
    );
    return acc;
  }, {});

  return {
    posts: Array.isArray(source.posts) && source.posts.length > 0 ? source.posts : fallbackScenarioData.posts,
    apiBase: typeof source.apiBase === "string" ? source.apiBase : DEFAULT_API_BASE,
    persoonNaam: typeof source.persoonNaam === "string" ? source.persoonNaam : "",
    geboortedatum: typeof source.geboortedatum === "string" ? source.geboortedatum : "",
    heeftPartner: Boolean(source.heeftPartner),
    partnerNaam: typeof source.partnerNaam === "string" ? source.partnerNaam : "",
    partnerGeboortedatum:
      typeof source.partnerGeboortedatum === "string" ? source.partnerGeboortedatum : "",
    jaarVan:
      typeof source.jaarVan === "string" ? source.jaarVan : fallbackScenarioData.jaarVan,
    jaarTot:
      typeof source.jaarTot === "string" ? source.jaarTot : fallbackScenarioData.jaarTot,
    scenarios,
    activeScenarioId,
    scenarioSnapshots,
    compareScenarioId: typeof source.compareScenarioId === "string" ? source.compareScenarioId : "",
    thirdScenarioId: typeof source.thirdScenarioId === "string" ? source.thirdScenarioId : "",
    comparisonResult:
      source.comparisonResult && typeof source.comparisonResult === "object" ? source.comparisonResult : null,
    activeScenarioSnapshot: scenarioSnapshots[activeScenarioId] || fallbackScenarioData,
  };
}

export function buildInputSignature(payload) {
  return JSON.stringify(payload);
}

export function extractFilename(contentDisposition) {
  if (!contentDisposition) {
    return "pensioen_rapport.xlsx";
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const quotedMatch = contentDisposition.match(/filename="([^"]+)"/i);
  if (quotedMatch?.[1]) {
    return quotedMatch[1];
  }

  const plainMatch = contentDisposition.match(/filename=([^;]+)/i);
  if (plainMatch?.[1]) {
    return plainMatch[1].trim();
  }

  return "pensioen_rapport.xlsx";
}

export function buildRequestPayload({
  posts,
  persoonNaam,
  geboortedatum,
  jaarVan,
  jaarTot,
  scenarioNaam,
  heeftPartner,
  partnerNaam,
  partnerGeboortedatum,
}) {
  const inkomstenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "inkomsten");
  const vermogenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "vermogen");

  const componenten = [];
  const incidentele_items = [];
  const vermogensitems = [];

  let jaarlijkse_inleg_sparen = 0;
  let jaarlijkse_inleg_beleggen = 0;
  let spaargeld_start = 0;
  let beleggingen_start = 0;

  const mapPersoon = (persoon, fallback) => {
    if (!persoon) {
      return fallback;
    }
    if (persoon === "P2" && !heeftPartner) {
      return fallback;
    }
    return persoon;
  };

  for (const post of inkomstenPosts) {
    const values = post.values;
    if (post.type === "eenmalige_inkomsten" || post.type === "eenmalige_uitgaven") {
      const bedrag = Math.abs(toAmount(values.bedrag));
      incidentele_items.push({
        datum: values.datum || `${jaarVan}-01-01`,
        bedrag: String(post.type === "eenmalige_uitgaven" ? -bedrag : bedrag),
        omschrijving: post.titel,
      });
      continue;
    }

    componenten.push({
      omschrijving: post.titel,
      categorie: CATEGORY_BY_TYPE[post.type],
      persoon: mapPersoon(values.persoon, "P1"),
      bedrag: String(Math.abs(toAmount(values.bedrag))),
      bedrag_type: post.type === "uitgave" ? "netto" : values.bedrag_type || "bruto",
      frequentie: values.frequentie || "maandelijks",
      beleggings_type: "sparen",
      begindatum: toIsoOrNull(values.startdatum),
      einddatum: toIsoOrNull(values.einddatum),
      groei_pct: String(toAmount(values.inflatie_pct)),
    });
  }

  for (const post of vermogenPosts) {
    const values = post.values;
    const type = VERMOGEN_TYPE_BY_POST[post.type];

    if (post.type === "sparen") {
      spaargeld_start += Math.max(0, toAmount(values.beginwaarde));
      jaarlijkse_inleg_sparen += Math.max(0, toAmount(values.inleg));
    }
    if (post.type === "beleggen") {
      beleggingen_start += Math.max(0, toAmount(values.beginwaarde));
      jaarlijkse_inleg_beleggen += Math.max(0, toAmount(values.inleg));
    }

    const item = {
      omschrijving: post.titel,
      type,
      persoon: mapPersoon(values.persoon, "Huishouden"),
      aanschafwaarde: String(Math.abs(toAmount(values.beginwaarde))),
      aanschafdatum: toIsoOrNull(values.startdatum),
      verkoopdatum: toIsoOrNull(values.einddatum),
      groei_pct: String(toAmount(values.groei_pct)),
      box3_belast: post.type !== "eigen_woning" && post.type !== "hypotheek",
    };

    if (post.type !== "hypotheek") {
      const peildatum = values.peildatum ?? values.startdatum ?? "";
      item.aanschafdatum = null;
      item.verkoopdatum = null;
      item.saldostanden = [
        { peildatum: peildatum || `${jaarVan}-01-01`, bedrag: item.aanschafwaarde },
        ...(Array.isArray(values.saldostanden) ? values.saldostanden.map(stand => ({
          peildatum: stand.peildatum || "", bedrag: String(stand.bedrag ?? ""),
        })) : []),
      ];
    }

    if (post.type === "sparen" || post.type === "beleggen") {
      item.jaarlijkse_inleg = String(Math.max(0, toAmount(values.inleg)));
    }

    if (post.type === "hypotheek") {
      item.is_primaire_woning = true;
      item.hypotheekrente_pct = String(Math.max(0, toAmount(values.rente_pct)));
      item.einddatum_aftrekbaarheid = toIsoOrNull(values.einddatum);
    }

    if (post.type === "eigen_woning") {
      item.woz_waarde = String(Math.abs(toAmount(values.beginwaarde)));
      item.woz_jaarlijkse_stijging_pct = String(toAmount(values.groei_pct));
    }

    vermogensitems.push(item);
  }


  return {
    scenario: {
      naam: scenarioNaam || "React UI scenario",
      spaargeld_start: String(spaargeld_start),
      beleggingen_start: String(beleggingen_start),
      jaarlijkse_inleg: "0",
      jaarlijkse_inleg_sparen: String(jaarlijkse_inleg_sparen),
      jaarlijkse_inleg_beleggen: String(jaarlijkse_inleg_beleggen),
      inflatie_pct: "2",
      box3_meenemen: true,
      componenten,
      incidentele_items,
      vermogensitems,
    },
    persoon1: {
      naam: persoonNaam,
      geboortedatum,
      heeft_partner: heeftPartner,
    },
    persoon2: heeftPartner
      ? {
          naam: partnerNaam,
          geboortedatum: partnerGeboortedatum,
          heeft_partner: true,
        }
      : null,
    records1: [],
    records2: [],
    jaar_van: Number(jaarVan),
    jaar_tot: Number(jaarTot),
    scenario_lijst: [],
  };
}

export function selectYearRows(cashflow) {
  const jaren = cashflow?.jaren;
  if (!Array.isArray(jaren)) {
    return [];
  }

  return jaren.map((jaar) => {
    const samenvatting = jaar?.jaar_samenvatting;
    if (!samenvatting || typeof samenvatting !== "object") {
      throw new Error(`API-outputcontract geschonden: jaar_samenvatting ontbreekt voor ${jaar?.jaar ?? "onbekend"}`);
    }
    return {
      jaar: Number(jaar.jaar),
      bruto: toAmount(samenvatting.bruto),
      belasting: toAmount(samenvatting.belasting),
      netto: toAmount(samenvatting.netto_inkomen ?? samenvatting.netto),
      cashflow: toAmount(samenvatting.netto_cashflow ?? samenvatting.netto),
      nettoPerMaand: toAmount(samenvatting.netto_inkomen_per_maand ?? samenvatting.netto_per_maand),
      vermogenEinde: toAmount(samenvatting.vermogen_einde_jaar),
      heeftNegatiefMaandvermogen: Array.isArray(jaar.maanden) && jaar.maanden.some(maand => Number(maand.vermogen_einde_maand) < 0),
    };
  });
}

export function buildScenarioComparisonRequest(ids, resolveRequest, jaarVan, jaarTot) {
  const selected = ids.filter(Boolean);
  if (selected.length < 2 || selected.length > 3 || new Set(selected).size !== selected.length) {
    throw new Error("Kies twee of drie verschillende scenario’s.");
  }
  const requests = selected.map(resolveRequest);
  if (new Set(requests.map(request => request.scenario.naam)).size !== requests.length) {
    throw new Error("Geef de te vergelijken scenario’s verschillende namen.");
  }
  return {
    scenarios: requests.map(request => request.scenario),
    persoon1: requests[0].persoon1, persoon2: requests[0].persoon2,
    records1: [], records2: [], jaar_van: Number(jaarVan), jaar_tot: Number(jaarTot),
  };
}

export function selectCurrentComparison(result, request) {
  return result?.inputSignature === JSON.stringify(request) ? result : null;
}

export function computeStopmomentSummary(jaarRows = [], geboortedatum = "") {
  const rows = Array.isArray(jaarRows) ? [...jaarRows].sort((a,b) => a.jaar - b.jaar) : [];
  const firstShortfallYear = rows.find(row => Number(row.cashflow) < 0)?.jaar ?? null;
  const firstNegativeWealthYear = rows.find(row => Number(row.vermogenEinde) < 0 || row.heeftNegatiefMaandvermogen)?.jaar ?? null;
  const birthYear = /^\d{4}-\d{2}-\d{2}$/.test(geboortedatum) ? Number(geboortedatum.slice(0,4)) : null;
  const wealthRow = birthYear === null ? null : rows.find(row => row.jaar === birthYear + 80);
  const wealthAt80 = wealthRow ? Number(wealthRow.vermogenEinde) : null;
  const stopMomentLabel = !rows.length ? "Onbekend" : firstNegativeWealthYear !== null
    ? "Vermogen negatief" : firstShortfallYear !== null ? "Interen op vermogen" : "Geen jaarlijks cashflowtekort";
  const summaryText = !rows.length ? "Bereken eerst je plan."
    : firstNegativeWealthYear !== null ? `In ${firstNegativeWealthYear} wordt een negatief vermogen berekend. Het plan vraagt aanpassing.`
    : firstShortfallYear !== null ? `In ${firstShortfallYear} is de vrije cashflow voor het eerst negatief. Dit vraagt dekking uit vermogen; latere jaren kunnen herstellen.`
    : "De berekende jaarlijkse vrije cashflow is nergens negatief. Dit bewijst niet dat eerder stoppen haalbaar is.";
  return {firstShortfallYear, firstNegativeWealthYear, stopMomentLabel, wealthAt80, summaryText};
}

export function buildScenarioDecisionCards(comparisonResult, activeScenarioName = "", compareScenarioName = "") {
  const scenarios = comparisonResult?.scenario_resultaten;
  if (!Array.isArray(scenarios) || scenarios.length < 2) return [];
  const active = scenarios.find(item => item.scenario_naam === activeScenarioName);
  if (!active || new Set(scenarios.map(item => item.scenario_naam)).size !== scenarios.length) return [];
  const bestName = comparisonResult.beste_scenario_netto?.scenario_naam;
  const knownWealth = item => comparisonResult.vermogen80Beschikbaar === false ? null
    : item.vermogen_op_80 == null ? null : decimalLike(item.vermogen_op_80);
  const baselineWealth = knownWealth(active);
  return [active, ...scenarios.filter(item => item !== active)].map(item => {
    const wealth = knownWealth(item);
    return {
      label: item === active ? "Actieve keuze" : "Alternatief",
      scenarioName: item.scenario_naam,
      nettoDelta: decimalLike(item.netto_per_maand_mediaan) - decimalLike(active.netto_per_maand_mediaan),
      vermogenDelta: wealth === null || baselineWealth === null ? null : wealth - baselineWealth,
      wealthAt80: wealth,
      shortfallYears: item.aantal_tekortjaren ?? null,
      isBest: item.scenario_naam === bestName,
      note: item.scenario_naam === bestName ? "Hoogste mediane vrije cashflow" : "Verschillen ten opzichte van de actieve keuze",
    };
  });
}

export function buildScenarioDecisionAdvice(comparisonResult, activeScenarioName = "", compareScenarioName = "") {
  const cards = buildScenarioDecisionCards(comparisonResult, activeScenarioName, compareScenarioName);
  if (!cards.length) return "Vergelijk opnieuw minstens twee verschillende scenario’s.";
  const best = cards.find(card => card.isBest);
  if (!best) return "De engine heeft geen beste scenario aangewezen. Vergelijk opnieuw.";
  if (cards.some(card => card.nettoDelta > best.nettoDelta)) return "De enginekeuze en de cashflowverschillen spreken elkaar tegen. Vergelijk opnieuw.";
  const amount = value => new Intl.NumberFormat("nl-NL", {minimumFractionDigits:2, maximumFractionDigits:2}).format(Math.abs(value));
  const delta = best.nettoDelta;
  const conclusion = delta > 0
    ? `${best.scenarioName} heeft volgens de engine € ${amount(delta)} meer mediane vrije cashflow per maand dan ${activeScenarioName}.`
    : delta === 0 ? `${best.scenarioName} heeft dezelfde mediane vrije cashflow als ${activeScenarioName}. Vergelijk bij gelijke cashflow ook vermogen en tekortjaren.`
    : `De enginekeuze en de cashflowverschillen spreken elkaar tegen. Vergelijk opnieuw voordat je een keuze maakt.`;
  const details = cards.map(card => {
    const wealth = card.wealthAt80 === null ? "vermogen op 80 niet beschikbaar binnen de berekeningsperiode"
      : `vermogen op 80: ${card.wealthAt80 < 0 ? "−" : ""}€ ${amount(card.wealthAt80)}`;
    const difference = card.vermogenDelta === null ? "" : ` (${card.vermogenDelta < 0 ? "−" : "+"}€ ${amount(card.vermogenDelta)} ten opzichte van actief)`;
    return `${card.scenarioName}: ${card.shortfallYears === null ? "aantal tekortjaren onbekend" : `${card.shortfallYears} tekortjaren`}, ${wealth}${difference}.`;
  }).join(" ");
  return `${conclusion} ${details} Kies niet alleen op cashflow: beoordeel ook de vermogensbuffer en de gewenste stopdatum. Dit is geen automatische aanbeveling om eerder te stoppen.`;
}

export function validateCalculationResponse(resultaat) {
  if (resultaat?.output_contract?.versie !== OUTPUT_CONTRACT_VERSION) {
    throw new Error("Onbekend of ontbrekend API-outputcontract.");
  }
  const jaren = resultaat?.cashflow?.jaren;
  if (!Array.isArray(jaren)) {
    throw new Error("API-outputcontract geschonden: cashflow.jaren ontbreekt.");
  }
  jaren.forEach((jaar) => {
    if (!jaar?.jaar_samenvatting || !jaar?.accountant_detail) {
      throw new Error(`API-outputcontract geschonden voor jaar ${jaar?.jaar ?? "onbekend"}.`);
    }
  });
  return resultaat;
}
