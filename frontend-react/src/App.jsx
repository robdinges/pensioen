import { useEffect, useMemo, useState } from "react";
import AccountantSection from "./components/AccountantSection";
import AppShell from "./components/layout/AppShell";
import ComponentsSection from "./components/ComponentsSection";
import ContextTopBar from "./components/layout/ContextTopBar";
import ReportSection from "./components/ReportSection";
import ResultsSection from "./components/ResultsSection";
import ScenarioSection from "./components/ScenarioSection";
import {
  analyzeMpoRows,
  parseCsvText,
  parseExcelBuffer,
  parseJsonText,
  parsePdfViaApi,
  rowsToPreview,
} from "./import/mpoImport";
import NewPostPicker from "./components/NewPostPicker";
import PostCard from "./components/PostCard";
import WizardSidebar from "./components/layout/WizardSidebar";
import MpoImportSection from "./components/MpoImportSection";
import { AppStateProvider, useAppState } from "./state/appState";

const FLOW_STEPS = [
  { id: "huishouden", label: "Huishouden" },
  { id: "personen", label: "Personen" },
  { id: "import", label: "Import" },
  { id: "periode", label: "Berekeningsperiode" },
  { id: "scenario", label: "Scenario's" },
  { id: "componenten", label: "Componenten" },
  { id: "resultaten", label: "Resultaten" },
  { id: "accountant", label: "Accountant" },
  { id: "rapport", label: "Rapport" },
];

const TYPE_CONFIG = {
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
    fields: ["persoon", "beginwaarde", "inleg", "groei_pct", "startdatum", "einddatum"],
  },
  beleggen: {
    section: "vermogen",
    label: "Beleggen",
    hint: "ETF, aandelen, beleggingsrekening.",
    fields: ["persoon", "beginwaarde", "inleg", "groei_pct", "startdatum", "einddatum"],
  },
  eigen_woning: {
    section: "vermogen",
    label: "Eigen woning",
    hint: "WOZ-waarde en verwachte waardegroei.",
    fields: ["persoon", "beginwaarde", "groei_pct", "startdatum", "einddatum"],
  },
  overige_bezittingen: {
    section: "vermogen",
    label: "Overige bezittingen",
    hint: "Auto, kunst, bedrijfsmiddelen, overig.",
    fields: ["persoon", "beginwaarde", "groei_pct", "startdatum", "einddatum"],
  },
  hypotheek: {
    section: "vermogen",
    label: "Schulden (hypotheek)",
    hint: "Hypotheekschuld met rente en aflossing.",
    fields: ["persoon", "beginwaarde", "rente_pct", "maandlast", "startdatum", "einddatum"],
  },
};

const FIELD_META = {
  persoon: { label: "Persoon", type: "select", options: ["P1", "P2", "Huishouden"], defaultValue: "P1" },
  bedrag: { label: "Bedrag", type: "number", step: "100", defaultValue: "0" },
  bedrag_type: { label: "Bedrag type", type: "select", options: ["bruto", "netto"], defaultValue: "bruto" },
  beginwaarde: { label: "Beginwaarde", type: "number", step: "1000", defaultValue: "0" },
  inleg: { label: "Periodieke inleg", type: "number", step: "100", defaultValue: "0" },
  maandlast: { label: "Maandlast", type: "number", step: "50", defaultValue: "0" },
  frequentie: {
    label: "Frequentie",
    type: "select",
    options: ["maandelijks", "kwartaal", "halfjaarlijks", "jaarlijks"],
    defaultValue: "maandelijks",
  },
  datum: { label: "Datum", type: "date", defaultValue: "" },
  startdatum: { label: "Begin datum", type: "date", defaultValue: "" },
  einddatum: { label: "Eind datum", type: "date", defaultValue: "" },
  groei_pct: { label: "Groei / rendement %", type: "number", step: "0.1", defaultValue: "0" },
  inflatie_pct: { label: "Inflatiecorrectie %", type: "number", step: "0.1", defaultValue: "2" },
  rente_pct: { label: "Rente %", type: "number", step: "0.1", defaultValue: "0" },
};

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

function euro(value) {
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value ?? 0);
}

function signedEuro(value) {
  const amount = decimalLike(value);
  if (amount === 0) {
    return euro(0);
  }
  return `${amount > 0 ? "+" : "-"}${euro(Math.abs(amount))}`;
}

function signedPercentagePoints(value) {
  const amount = decimalLike(value);
  return `${amount > 0 ? "+" : ""}${amount.toFixed(1)} pp`;
}

function emptyValuesFor(type) {
  const fields = TYPE_CONFIG[type].fields;
  return fields.reduce((acc, field) => {
    acc[field] = FIELD_META[field].defaultValue;
    return acc;
  }, {});
}

function createPost(type) {
  return {
    id: crypto.randomUUID(),
    type,
    titel: TYPE_CONFIG[type].label,
    values: emptyValuesFor(type),
  };
}

function createDefaultScenarioData() {
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

function decimalLike(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

function extractFilename(contentDisposition) {
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

function buildRequestPayload({
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
  const sparenRendementen = [];
  const beleggenRendementen = [];

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
      sparenRendementen.push(toAmount(values.groei_pct));
    }
    if (post.type === "beleggen") {
      beleggingen_start += Math.max(0, toAmount(values.beginwaarde));
      jaarlijkse_inleg_beleggen += Math.max(0, toAmount(values.inleg));
      beleggenRendementen.push(toAmount(values.groei_pct));
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

  const rendement_sparen_pct =
    sparenRendementen.length > 0
      ? sparenRendementen.reduce((sum, value) => sum + value, 0) / sparenRendementen.length
      : 0;
  const rendement_beleggen_pct =
    beleggenRendementen.length > 0
      ? beleggenRendementen.reduce((sum, value) => sum + value, 0) / beleggenRendementen.length
      : 0;

  return {
    scenario: {
      naam: scenarioNaam || "React UI scenario",
      spaargeld_start: String(spaargeld_start),
      beleggingen_start: String(beleggingen_start),
      jaarlijkse_inleg: "0",
      jaarlijkse_inleg_sparen: String(jaarlijkse_inleg_sparen),
      jaarlijkse_inleg_beleggen: String(jaarlijkse_inleg_beleggen),
      rendement_sparen_pct: String(rendement_sparen_pct),
      rendement_beleggen_pct: String(rendement_beleggen_pct),
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

function aggregateYearRows(cashflow) {
  const jaren = cashflow?.jaren;
  if (!Array.isArray(jaren)) {
    return [];
  }

  return jaren.map((jaar) => {
    const maanden = Array.isArray(jaar.maanden) ? jaar.maanden : [];
    let bruto = 0;
    let belasting = 0;
    let netto = 0;

    maanden.forEach((m) => {
      const brutoMaand =
        toAmount(m.arbeid_p1_bruto) +
        toAmount(m.arbeid_p2_bruto) +
        toAmount(m.aow_p1_bruto) +
        toAmount(m.aow_p2_bruto) +
        toAmount(m.pensioen_p1_bruto) +
        toAmount(m.pensioen_p2_bruto) +
        toAmount(m.lijfrente_bruto) +
        toAmount(m.rente_bruto) +
        toAmount(m.overig_bruto);

      const belastingMaand =
        toAmount(m.belasting_p1) +
        toAmount(m.belasting_p2) +
        toAmount(m.box3_heffing);

      const kortingMaand = toAmount(m.heffingskorting_p1) + toAmount(m.heffingskorting_p2);
      const nettoMaand =
        brutoMaand +
        toAmount(m.inkomen_componenten_netto) -
        belastingMaand +
        kortingMaand -
        toAmount(m.inhoudingen) -
        toAmount(m.huishoudelijke_uitgaven) +
        toAmount(m.eenmalig_ontvangst) -
        toAmount(m.eenmalig_uitgave);

      bruto += brutoMaand;
      belasting += belastingMaand;
      netto += nettoMaand;
    });

    const vermogenEinde = maanden.length ? toAmount(maanden[maanden.length - 1].vermogen_einde_maand) : 0;

    return {
      jaar: jaar.jaar,
      bruto,
      belasting,
      netto,
      nettoPerMaand: maanden.length ? netto / maanden.length : 0,
      vermogenEinde,
    };
  });
}

function SectionHeader({ title, description }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function AppContent() {
  const { state, actions } = useAppState();
  const initialHouseholdId = useMemo(() => crypto.randomUUID(), []);
  const initialScenarioId = useMemo(() => crypto.randomUUID(), []);

  const [households, setHouseholds] = useState([{ id: initialHouseholdId, name: "Standaard huishouden" }]);
  const [activeHouseholdId, setActiveHouseholdId] = useState(initialHouseholdId);
  const [newHouseholdName, setNewHouseholdName] = useState("");
  const [scenarios, setScenarios] = useState([{ id: initialScenarioId, naam: "Basisscenario" }]);
  const [activeScenarioId, setActiveScenarioId] = useState(initialScenarioId);
  const [newScenarioName, setNewScenarioName] = useState("");

  const [posts, setPosts] = useState([createPost("loon"), createPost("sparen")]);
  const [inkomenType, setInkomenType] = useState("uitkering");
  const [vermogenType, setVermogenType] = useState("beleggen");
  const [apiBase, setApiBase] = useState("/api/v1");
  const [persoonNaam, setPersoonNaam] = useState("Jan Jansen");
  const [geboortedatum, setGeboortedatum] = useState("1963-03-15");
  const [heeftPartner, setHeeftPartner] = useState(false);
  const [partnerNaam, setPartnerNaam] = useState("");
  const [partnerGeboortedatum, setPartnerGeboortedatum] = useState("");
  const [jaarVan, setJaarVan] = useState(String(new Date().getFullYear()));
  const [jaarTot, setJaarTot] = useState(String(new Date().getFullYear() + 20));
  const [isLoading, setIsLoading] = useState(false);
  const [isReportLoading, setIsReportLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [reportErrorMessage, setReportErrorMessage] = useState("");
  const [importErrorMessages, setImportErrorMessages] = useState({ P1: "", P2: "" });
  const [importInfoMessages, setImportInfoMessages] = useState({ P1: "", P2: "" });
  const [isImporting, setIsImporting] = useState({ P1: false, P2: false });
  const [importBestandP1Naam, setImportBestandP1Naam] = useState("");
  const [importBestandP2Naam, setImportBestandP2Naam] = useState("");
  const [importPreviewP1, setImportPreviewP1] = useState([]);
  const [importPreviewP2, setImportPreviewP2] = useState([]);
  const [importWarningsP1, setImportWarningsP1] = useState([]);
  const [importWarningsP2, setImportWarningsP2] = useState([]);
  const [importStatsP1, setImportStatsP1] = useState(null);
  const [importStatsP2, setImportStatsP2] = useState(null);
  const [resultaat, setResultaat] = useState(null);
  const [inputSignatureAtCalculation, setInputSignatureAtCalculation] = useState("");
  const [compareScenarioId, setCompareScenarioId] = useState("");
  const [comparisonResult, setComparisonResult] = useState(null);
  const [comparisonError, setComparisonError] = useState("");
  const [isComparing, setIsComparing] = useState(false);
  const [scenarioSnapshots, setScenarioSnapshots] = useState({
    [initialScenarioId]: createDefaultScenarioData(),
  });
  const [householdSnapshots, setHouseholdSnapshots] = useState({
    [initialHouseholdId]: {
      posts: [createPost("loon"), createPost("sparen")],
      apiBase: "/api/v1",
      persoonNaam: "Jan Jansen",
      geboortedatum: "1963-03-15",
      heeftPartner: false,
      partnerNaam: "",
      partnerGeboortedatum: "",
      scenarios: [{ id: initialScenarioId, naam: "Basisscenario" }],
      activeScenarioId: initialScenarioId,
      scenarioSnapshots: {
        [initialScenarioId]: createDefaultScenarioData(),
      },
      compareScenarioId: "",
      comparisonResult: null,
      importBestandP1Naam: "",
      importBestandP2Naam: "",
      importPreviewP1: [],
      importPreviewP2: [],
      importWarningsP1: [],
      importWarningsP2: [],
      importStatsP1: null,
      importStatsP2: null,
      jaarVan: String(new Date().getFullYear()),
      jaarTot: String(new Date().getFullYear() + 20),
      resultaat: null,
      inputSignatureAtCalculation: "",
      calculationStatus: "idle",
    },
  });
  const [hydrated, setHydrated] = useState(false);

  const activeStep = state.activeStep;

  const inkomstenTypes = useMemo(
    () => Object.keys(TYPE_CONFIG).filter((key) => TYPE_CONFIG[key].section === "inkomsten"),
    [],
  );
  const vermogenTypes = useMemo(
    () => Object.keys(TYPE_CONFIG).filter((key) => TYPE_CONFIG[key].section === "vermogen"),
    [],
  );

  const inkomstenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "inkomsten");
  const vermogenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "vermogen");
  const activeHousehold = households.find((household) => household.id === activeHouseholdId) || households[0];
  const activeHouseholdName = activeHousehold?.name || "Huishouden";
  const activeScenario =
    scenarios.find((scenario) => scenario.id === activeScenarioId) ||
    scenarios[0] ||
    null;
  const activeScenarioName = activeScenario?.naam || "Basisscenario";
  const compareScenario = scenarios.find((scenario) => scenario.id === compareScenarioId) || null;
  const compareScenarioName = compareScenario?.naam || "";
  const comparisonSummary = useMemo(() => {
    const results = comparisonResult?.scenario_resultaten;
    if (!Array.isArray(results) || results.length < 2 || !compareScenarioName) {
      return null;
    }

    const activeItem = results.find((item) => item.scenario_naam === activeScenarioName);
    const compareItem = results.find((item) => item.scenario_naam === compareScenarioName);
    if (!activeItem || !compareItem) {
      return null;
    }

    return {
      nettoDelta: decimalLike(compareItem.netto_per_maand_mediaan) - decimalLike(activeItem.netto_per_maand_mediaan),
      vermogen80Delta: decimalLike(compareItem.vermogen_op_80) - decimalLike(activeItem.vermogen_op_80),
      belastingdrukDelta:
        decimalLike(compareItem.gemiddelde_belastingdruk) - decimalLike(activeItem.gemiddelde_belastingdruk),
    };
  }, [comparisonResult, activeScenarioName, compareScenarioName]);

  const jaarVanNum = Number(jaarVan);
  const jaarTotNum = Number(jaarTot);
  const periodeValidatie = [];
  if (!Number.isInteger(jaarVanNum) || jaarVanNum < 1900 || jaarVanNum > 2200) {
    periodeValidatie.push("Jaar van moet een volledig jaar tussen 1900 en 2200 zijn.");
  }
  if (!Number.isInteger(jaarTotNum) || jaarTotNum < 1900 || jaarTotNum > 2200) {
    periodeValidatie.push("Jaar tot moet een volledig jaar tussen 1900 en 2200 zijn.");
  }
  if (Number.isInteger(jaarVanNum) && Number.isInteger(jaarTotNum) && jaarTotNum < jaarVanNum) {
    periodeValidatie.push("Jaar tot mag niet voor jaar van liggen.");
  }
  const periodeIsValid = periodeValidatie.length === 0;
  const personenIsValid = Boolean(
    persoonNaam &&
      geboortedatum &&
      (!heeftPartner || (partnerNaam && partnerGeboortedatum)),
  );
  const isImportingP1 = isImporting.P1;
  const isImportingP2 = isImporting.P2;

  const setImportErrorFor = (persoonCode, message) => {
    setImportErrorMessages((prev) => ({ ...prev, [persoonCode]: message }));
  };

  const setImportInfoFor = (persoonCode, message) => {
    setImportInfoMessages((prev) => ({ ...prev, [persoonCode]: message }));
  };

  const setImportingFor = (persoonCode, value) => {
    setIsImporting((prev) => ({ ...prev, [persoonCode]: value }));
  };

  const updatePost = (id, key, value, isRoot = false) => {
    setPosts((prev) =>
      prev.map((post) => {
        if (post.id !== id) {
          return post;
        }
        if (isRoot) {
          return { ...post, [key]: value };
        }
        return { ...post, values: { ...post.values, [key]: value } };
      }),
    );
  };

  const removePost = (id) => setPosts((prev) => prev.filter((post) => post.id !== id));
  const addPost = (type) => setPosts((prev) => [...prev, createPost(type)]);

  const buildCurrentScenarioSnapshot = () => ({
    posts,
    jaarVan,
    jaarTot,
    importBestandP1Naam,
    importBestandP2Naam,
    importPreviewP1,
    importPreviewP2,
    importWarningsP1,
    importWarningsP2,
    importStatsP1,
    importStatsP2,
    resultaat,
    inputSignatureAtCalculation,
    calculationStatus: state.calculationStatus,
  });

  const scenarioRequestFromSnapshot = (snapshot, scenarioNaam) => {
    const request = buildRequestPayload({
      posts: snapshot.posts,
      persoonNaam,
      geboortedatum,
      jaarVan: snapshot.jaarVan,
      jaarTot: snapshot.jaarTot,
      scenarioNaam,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
    });
    return request;
  };

  const hydrateFromScenarioSnapshot = (snapshot) => {
    const source = snapshot || createDefaultScenarioData();
    setPosts(Array.isArray(source.posts) && source.posts.length > 0 ? source.posts : [createPost("loon"), createPost("sparen")]);
    setJaarVan(typeof source.jaarVan === "string" ? source.jaarVan : String(new Date().getFullYear()));
    setJaarTot(
      typeof source.jaarTot === "string"
        ? source.jaarTot
        : String(new Date().getFullYear() + 20),
    );
    setImportBestandP1Naam(typeof source.importBestandP1Naam === "string" ? source.importBestandP1Naam : "");
    setImportBestandP2Naam(typeof source.importBestandP2Naam === "string" ? source.importBestandP2Naam : "");
    setImportPreviewP1(Array.isArray(source.importPreviewP1) ? source.importPreviewP1 : []);
    setImportPreviewP2(Array.isArray(source.importPreviewP2) ? source.importPreviewP2 : []);
    setImportWarningsP1(Array.isArray(source.importWarningsP1) ? source.importWarningsP1 : []);
    setImportWarningsP2(Array.isArray(source.importWarningsP2) ? source.importWarningsP2 : []);
    setImportStatsP1(source.importStatsP1 && typeof source.importStatsP1 === "object" ? source.importStatsP1 : null);
    setImportStatsP2(source.importStatsP2 && typeof source.importStatsP2 === "object" ? source.importStatsP2 : null);
    setResultaat(source.resultaat || null);
    setInputSignatureAtCalculation(
      typeof source.inputSignatureAtCalculation === "string" ? source.inputSignatureAtCalculation : "",
    );
    actions.setCalcStatus(
      typeof source.calculationStatus === "string" ? source.calculationStatus : "idle",
    );
  };

  const buildCurrentSnapshot = () => ({
    posts,
    apiBase,
    persoonNaam,
    geboortedatum,
    heeftPartner,
    partnerNaam,
    partnerGeboortedatum,
    scenarios,
    activeScenarioId,
    scenarioSnapshots,
    compareScenarioId,
    comparisonResult,
    importBestandP1Naam,
    importBestandP2Naam,
    importPreviewP1,
    importPreviewP2,
    importWarningsP1,
    importWarningsP2,
    importStatsP1,
    importStatsP2,
    jaarVan,
    jaarTot,
    resultaat,
    inputSignatureAtCalculation,
    calculationStatus: state.calculationStatus,
  });

  const hydrateFromSnapshot = (snapshot) => {
    const source = snapshot || {};
    if (Array.isArray(source.posts) && source.posts.length > 0) {
      setPosts(source.posts);
    } else {
      setPosts([createPost("loon"), createPost("sparen")]);
    }
    setApiBase(typeof source.apiBase === "string" ? source.apiBase : "/api/v1");
    setPersoonNaam(typeof source.persoonNaam === "string" ? source.persoonNaam : "");
    setGeboortedatum(typeof source.geboortedatum === "string" ? source.geboortedatum : "");
    setHeeftPartner(Boolean(source.heeftPartner));
    setPartnerNaam(typeof source.partnerNaam === "string" ? source.partnerNaam : "");
    setPartnerGeboortedatum(
      typeof source.partnerGeboortedatum === "string" ? source.partnerGeboortedatum : "",
    );
    const loadedScenarios =
      Array.isArray(source.scenarios) && source.scenarios.length > 0
        ? source.scenarios
        : [{ id: crypto.randomUUID(), naam: "Basisscenario" }];
    setScenarios(loadedScenarios);
    const loadedActiveScenarioId =
      typeof source.activeScenarioId === "string" &&
      loadedScenarios.some((scenario) => scenario.id === source.activeScenarioId)
        ? source.activeScenarioId
        : loadedScenarios[0].id;
    setActiveScenarioId(loadedActiveScenarioId);

    const fallbackScenarioData = {
      ...createDefaultScenarioData(),
      posts: Array.isArray(source.posts) && source.posts.length > 0 ? source.posts : [createPost("loon"), createPost("sparen")],
      jaarVan: typeof source.jaarVan === "string" ? source.jaarVan : String(new Date().getFullYear()),
      jaarTot:
        typeof source.jaarTot === "string"
          ? source.jaarTot
          : String(new Date().getFullYear() + 20),
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
    };

    const loadedScenarioSnapshots =
      source.scenarioSnapshots && typeof source.scenarioSnapshots === "object"
        ? source.scenarioSnapshots
        : { [loadedActiveScenarioId]: fallbackScenarioData };

    setScenarioSnapshots(loadedScenarioSnapshots);
    setCompareScenarioId(
      typeof source.compareScenarioId === "string" ? source.compareScenarioId : "",
    );
    setComparisonResult(
      source.comparisonResult && typeof source.comparisonResult === "object"
        ? source.comparisonResult
        : null,
    );
    hydrateFromScenarioSnapshot(
      loadedScenarioSnapshots[loadedActiveScenarioId] || fallbackScenarioData,
    );
  };

  const switchHousehold = (nextHouseholdId) => {
    if (!nextHouseholdId || nextHouseholdId === activeHouseholdId) {
      return;
    }

    const updatedSnapshots = {
      ...householdSnapshots,
      [activeHouseholdId]: buildCurrentSnapshot(),
    };
    const nextSnapshot = updatedSnapshots[nextHouseholdId] || null;

    setHouseholdSnapshots(updatedSnapshots);

    setActiveHouseholdId(nextHouseholdId);
    hydrateFromSnapshot(nextSnapshot);
  };

  const addHousehold = () => {
    const label = newHouseholdName.trim() || `Huishouden ${households.length + 1}`;
    const nextHouseholdId = crypto.randomUUID();
    const initialScenario = { id: crypto.randomUUID(), naam: "Basisscenario" };
    const initialScenarioData = createDefaultScenarioData();
    const snapshot = {
      posts: initialScenarioData.posts,
      apiBase: "/api/v1",
      persoonNaam: "",
      geboortedatum: "",
      heeftPartner: false,
      partnerNaam: "",
      partnerGeboortedatum: "",
      scenarios: [initialScenario],
      activeScenarioId: initialScenario.id,
      scenarioSnapshots: {
        [initialScenario.id]: initialScenarioData,
      },
      compareScenarioId: "",
      comparisonResult: null,
      importBestandP1Naam: initialScenarioData.importBestandP1Naam,
      importBestandP2Naam: initialScenarioData.importBestandP2Naam,
      importPreviewP1: initialScenarioData.importPreviewP1,
      importPreviewP2: initialScenarioData.importPreviewP2,
      importWarningsP1: initialScenarioData.importWarningsP1,
      importWarningsP2: initialScenarioData.importWarningsP2,
      importStatsP1: initialScenarioData.importStatsP1,
      importStatsP2: initialScenarioData.importStatsP2,
      jaarVan: initialScenarioData.jaarVan,
      jaarTot: initialScenarioData.jaarTot,
      resultaat: initialScenarioData.resultaat,
      inputSignatureAtCalculation: initialScenarioData.inputSignatureAtCalculation,
      calculationStatus: initialScenarioData.calculationStatus,
    };

    setHouseholds((prev) => [...prev, { id: nextHouseholdId, name: label }]);
    setHouseholdSnapshots((prev) => ({
      ...prev,
      [activeHouseholdId]: buildCurrentSnapshot(),
      [nextHouseholdId]: snapshot,
    }));
    setActiveHouseholdId(nextHouseholdId);
    setNewHouseholdName("");
    hydrateFromSnapshot(snapshot);
  };

  const removeActiveHousehold = () => {
    if (households.length <= 1) {
      return;
    }

    const remaining = households.filter((household) => household.id !== activeHouseholdId);
    const nextActiveId = remaining[0].id;
    const nextSnapshot = householdSnapshots[nextActiveId] || null;

    setHouseholds(remaining);
    setHouseholdSnapshots((prev) => {
      const clone = { ...prev };
      delete clone[activeHouseholdId];
      return clone;
    });
    setActiveHouseholdId(nextActiveId);
    hydrateFromSnapshot(nextSnapshot);
  };

  const renameActiveHousehold = (name) => {
    setHouseholds((prev) =>
      prev.map((household) =>
        household.id === activeHouseholdId ? { ...household, name } : household,
      ),
    );
  };

  const addScenario = () => {
    const label = newScenarioName.trim() || `Scenario ${scenarios.length + 1}`;
    const nextId = crypto.randomUUID();
    const currentScenarioData = buildCurrentScenarioSnapshot();
    setScenarios((prev) => [...prev, { id: nextId, naam: label }]);
    const clonedData = JSON.parse(JSON.stringify(currentScenarioData));
    clonedData.resultaat = null;
    clonedData.inputSignatureAtCalculation = "";
    clonedData.calculationStatus = "idle";
    setScenarioSnapshots((prev) => ({
      ...prev,
      [activeScenarioId]: currentScenarioData,
      [nextId]: clonedData,
    }));
    setActiveScenarioId(nextId);
    hydrateFromScenarioSnapshot(clonedData);
    setNewScenarioName("");
  };

  const switchScenario = (nextScenarioId) => {
    if (!nextScenarioId || nextScenarioId === activeScenarioId) {
      return;
    }

    const currentScenarioData = buildCurrentScenarioSnapshot();
    const updatedSnapshots = {
      ...scenarioSnapshots,
      [activeScenarioId]: currentScenarioData,
    };
    const targetSnapshot =
      updatedSnapshots[nextScenarioId] || JSON.parse(JSON.stringify(createDefaultScenarioData()));

    setScenarioSnapshots(updatedSnapshots);
    setActiveScenarioId(nextScenarioId);
    hydrateFromScenarioSnapshot(targetSnapshot);
  };

  const removeActiveScenario = () => {
    if (scenarios.length <= 1) {
      return;
    }
    const remaining = scenarios.filter((scenario) => scenario.id !== activeScenarioId);
    setScenarios(remaining);
    const nextId = remaining[0].id;
    const nextSnapshot = scenarioSnapshots[nextId] || createDefaultScenarioData();
    setScenarioSnapshots((prev) => {
      const clone = { ...prev };
      delete clone[activeScenarioId];
      return clone;
    });
    setActiveScenarioId(nextId);
    hydrateFromScenarioSnapshot(nextSnapshot);
  };

  const renameActiveScenario = (name) => {
    setScenarios((prev) =>
      prev.map((scenario) =>
        scenario.id === activeScenarioId ? { ...scenario, naam: name } : scenario,
      ),
    );
  };

  const duplicateActiveScenario = () => {
    const baseName = activeScenarioName?.trim() || "Scenario";
    const nextId = crypto.randomUUID();
    const cloneName = `${baseName} kopie`;
    const currentScenarioData = buildCurrentScenarioSnapshot();
    const clonedData = JSON.parse(JSON.stringify(currentScenarioData));
    clonedData.resultaat = null;
    clonedData.inputSignatureAtCalculation = "";
    clonedData.calculationStatus = "idle";

    setScenarios((prev) => [...prev, { id: nextId, naam: cloneName }]);
    setScenarioSnapshots((prev) => ({
      ...prev,
      [activeScenarioId]: currentScenarioData,
      [nextId]: clonedData,
    }));
    setActiveScenarioId(nextId);
    hydrateFromScenarioSnapshot(clonedData);
  };

  const runScenarioComparison = async () => {
    if (!compareScenarioId) {
      setComparisonError("Kies eerst een tweede scenario om te vergelijken.");
      return;
    }

    const currentSnapshot = buildCurrentScenarioSnapshot();
    const otherScenario = scenarios.find((scenario) => scenario.id === compareScenarioId);
    const otherSnapshot = scenarioSnapshots[compareScenarioId];

    if (!otherScenario || !otherSnapshot) {
      setComparisonError("Het gekozen scenario kon niet worden geladen.");
      return;
    }

    setIsComparing(true);
    setComparisonError("");

    try {
      const activeRequest = scenarioRequestFromSnapshot(currentSnapshot, activeScenarioName);
      const otherRequest = scenarioRequestFromSnapshot(otherSnapshot, otherScenario.naam);
      const jaarVanVergelijking = Math.min(Number(currentSnapshot.jaarVan), Number(otherSnapshot.jaarVan));
      const jaarTotVergelijking = Math.max(Number(currentSnapshot.jaarTot), Number(otherSnapshot.jaarTot));

      const response = await fetch(`${apiBase}/vergelijkingen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenarios: [activeRequest.scenario, otherRequest.scenario],
          persoon1: activeRequest.persoon1,
          persoon2: activeRequest.persoon2,
          records1: [],
          records2: [],
          jaar_van: jaarVanVergelijking,
          jaar_tot: jaarTotVergelijking,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = data?.detail;
        if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
          setComparisonError(detail[0].msg);
        } else if (typeof detail === "string") {
          setComparisonError(detail);
        } else if (detail?.message) {
          setComparisonError(detail.message);
        } else {
          setComparisonError(`Scenariovergelijking mislukt (${response.status})`);
        }
        return;
      }

      setComparisonResult({
        ...data?.vergelijking,
        jaar_van: jaarVanVergelijking,
        jaar_tot: jaarTotVergelijking,
      });
    } catch (err) {
      setComparisonError(err instanceof Error ? err.message : "Onbekende fout bij scenariovergelijking");
    } finally {
      setIsComparing(false);
    }
  };

  const importMpoFileForPersoon = async (file, persoonCode) => {
    if (!file) {
      setImportErrorFor(persoonCode, "Selecteer eerst een MPO-bestand.");
      setImportInfoFor(persoonCode, "");
      return;
    }

    const extension = file.name.toLowerCase().split(".").pop();
    if (extension !== "csv" && extension !== "json" && extension !== "xlsx" && extension !== "xls" && extension !== "pdf") {
      setImportErrorFor(persoonCode, "Alleen CSV, Excel (.xlsx/.xls), JSON en PDF worden ondersteund in de React importstap.");
      setImportInfoFor(persoonCode, "");
      return;
    }

    try {
      setImportingFor(persoonCode, true);
      setImportErrorFor(persoonCode, "");
      setImportInfoFor(persoonCode, `Importeren van ${file.name}...`);
      let rows = [];
      if (extension === "csv") {
        const content = await file.text();
        rows = parseCsvText(content);
      } else if (extension === "json") {
        const content = await file.text();
        rows = parseJsonText(content);
      } else if (extension === "pdf") {
        rows = await parsePdfViaApi(file, apiBase);
      } else {
        const buffer = await file.arrayBuffer();
        rows = await parseExcelBuffer(buffer);
      }

      const preview = rowsToPreview(rows);
      const analyse = analyzeMpoRows(rows, persoonCode, ({ persoonCode: code, title, bedrag, ingangsdatum, einddatum, indexatie }) => ({
        id: crypto.randomUUID(),
        type: "pensioen",
        titel: title,
        source: "mpo",
        values: {
          ...emptyValuesFor("pensioen"),
          persoon: code,
          bedrag: String(bedrag),
          bedrag_type: "bruto",
          frequentie: "jaarlijks",
          startdatum: ingangsdatum,
          einddatum,
          inflatie_pct: String(indexatie),
        },
      }));
      const importedPosts = analyse.posts;

      if (importedPosts.length === 0) {
        if (persoonCode === "P1") {
          setImportWarningsP1(analyse.warnings);
          setImportStatsP1(analyse.stats);
          setImportPreviewP1(preview);
        } else {
          setImportWarningsP2(analyse.warnings);
          setImportStatsP2(analyse.stats);
          setImportPreviewP2(preview);
        }
        setImportInfoFor(persoonCode, `Geen bruikbare pensioenregels gevonden in ${file.name}.`);
        return;
      }

      setPosts((prev) => {
        const withoutOldMpoForPerson = prev.filter(
          (post) => !(post.type === "pensioen" && post.source === "mpo" && post.values?.persoon === persoonCode),
        );
        return [...withoutOldMpoForPerson, ...importedPosts];
      });

      if (persoonCode === "P1") {
        setImportBestandP1Naam(file.name);
        setImportPreviewP1(preview);
        setImportWarningsP1(analyse.warnings);
        setImportStatsP1(analyse.stats);
      } else {
        setImportBestandP2Naam(file.name);
        setImportPreviewP2(preview);
        setImportWarningsP2(analyse.warnings);
        setImportStatsP2(analyse.stats);
      }

      setImportInfoFor(
        persoonCode,
        `${importedPosts.length} pensioenregel(s) geïmporteerd voor ${persoonCode} (bronregels: ${analyse.stats.bronregels}).`,
      );
      setErrorMessage("");
    } catch (err) {
      setImportInfoFor(persoonCode, "");
      setImportErrorFor(persoonCode, err instanceof Error ? err.message : "Onbekende fout bij import.");
    } finally {
      setImportingFor(persoonCode, false);
    }
  };

  const payloadPreview = {
    inkomsten_uitgaven: inkomstenPosts.map((post) => ({ id: post.id, type: post.type, titel: post.titel, ...post.values })),
    vermogen: vermogenPosts.map((post) => ({ id: post.id, type: post.type, titel: post.titel, ...post.values })),
  };

  const jaarRows = useMemo(() => aggregateYearRows(resultaat?.cashflow), [resultaat]);
  const inputSignature = useMemo(
    () =>
      JSON.stringify({
        activeHouseholdId,
        posts,
        apiBase,
        persoonNaam,
        geboortedatum,
        heeftPartner,
        partnerNaam,
        partnerGeboortedatum,
        scenarios,
        activeScenarioId,
        importBestandP1Naam,
        importBestandP2Naam,
        importPreviewP1,
        importPreviewP2,
        importWarningsP1,
        importWarningsP2,
        importStatsP1,
        importStatsP2,
        jaarVan,
        jaarTot,
      }),
    [
      activeHouseholdId,
      posts,
      apiBase,
      persoonNaam,
      geboortedatum,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
      scenarios,
      activeScenarioId,
      compareScenarioId,
      comparisonResult,
      importBestandP1Naam,
      importBestandP2Naam,
      importPreviewP1,
      importPreviewP2,
      importWarningsP1,
      importWarningsP2,
      importStatsP1,
      importStatsP2,
      jaarVan,
      jaarTot,
    ],
  );

  useEffect(() => {
    try {
      const raw = localStorage.getItem("pensioen-ui-session-v1");
      if (raw) {
        const parsed = JSON.parse(raw);

        const parsedHouseholds = Array.isArray(parsed.households) ? parsed.households : null;
        const parsedSnapshots = parsed.householdSnapshots && typeof parsed.householdSnapshots === "object"
          ? parsed.householdSnapshots
          : null;

        if (parsedHouseholds && parsedHouseholds.length > 0 && parsedSnapshots) {
          setHouseholds(parsedHouseholds);
          setHouseholdSnapshots(parsedSnapshots);
          const persistedActiveId =
            typeof parsed.activeHouseholdId === "string" &&
            parsedHouseholds.some((item) => item.id === parsed.activeHouseholdId)
              ? parsed.activeHouseholdId
              : parsedHouseholds[0].id;
          setActiveHouseholdId(persistedActiveId);
          hydrateFromSnapshot(parsedSnapshots[persistedActiveId]);
        } else {
          if (Array.isArray(parsed.posts) && parsed.posts.length > 0) {
            setPosts(parsed.posts);
          }
          if (typeof parsed.apiBase === "string") {
            setApiBase(parsed.apiBase);
          }
          if (typeof parsed.persoonNaam === "string") {
            setPersoonNaam(parsed.persoonNaam);
          }
          if (typeof parsed.geboortedatum === "string") {
            setGeboortedatum(parsed.geboortedatum);
          }
          if (typeof parsed.heeftPartner === "boolean") {
            setHeeftPartner(parsed.heeftPartner);
          }
          if (typeof parsed.partnerNaam === "string") {
            setPartnerNaam(parsed.partnerNaam);
          }
          if (typeof parsed.partnerGeboortedatum === "string") {
            setPartnerGeboortedatum(parsed.partnerGeboortedatum);
          }
          if (typeof parsed.jaarVan === "string") {
            setJaarVan(parsed.jaarVan);
          }
          if (typeof parsed.jaarTot === "string") {
            setJaarTot(parsed.jaarTot);
          }
          if (parsed.resultaat) {
            setResultaat(parsed.resultaat);
          }
          if (typeof parsed.inputSignatureAtCalculation === "string") {
            setInputSignatureAtCalculation(parsed.inputSignatureAtCalculation);
          }
        }

        if (typeof parsed.activeStep === "string") {
          actions.setActiveStep(parsed.activeStep);
        }
        actions.setContext({
          currentHousehold: parsed.currentHousehold || activeHouseholdName,
          activeScenario: parsed.activeScenario,
        });
        if (typeof parsed.calculationStatus === "string") {
          actions.setCalcStatus(parsed.calculationStatus);
        }
      }
    } catch {
      // Ignore invalid cache state and continue.
    }
    setHydrated(true);
  }, [actions]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    actions.setAutosaveStatus("saving");
    const payload = {
      households,
      activeHouseholdId,
      householdSnapshots: {
        ...householdSnapshots,
        [activeHouseholdId]: buildCurrentSnapshot(),
      },
      posts,
      apiBase,
      persoonNaam,
      geboortedatum,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
      scenarios,
      activeScenarioId,
      importBestandP1Naam,
      importBestandP2Naam,
      importPreviewP1,
      importPreviewP2,
      importWarningsP1,
      importWarningsP2,
      importStatsP1,
      importStatsP2,
      jaarVan,
      jaarTot,
      resultaat,
      inputSignatureAtCalculation,
      activeStep: state.activeStep,
      currentHousehold: activeHouseholdName,
      activeScenario: activeScenarioName,
      calculationStatus: state.calculationStatus,
    };
    localStorage.setItem("pensioen-ui-session-v1", JSON.stringify(payload));

    const timer = setTimeout(() => actions.setAutosaveStatus("saved"), 250);
    return () => clearTimeout(timer);
  }, [
    hydrated,
    households,
    activeHouseholdId,
    householdSnapshots,
    posts,
    apiBase,
    persoonNaam,
    geboortedatum,
    heeftPartner,
    partnerNaam,
    partnerGeboortedatum,
    scenarios,
    activeScenarioId,
    compareScenarioId,
    comparisonResult,
    importBestandP1Naam,
    importBestandP2Naam,
    importPreviewP1,
    importPreviewP2,
    importWarningsP1,
    importWarningsP2,
    importStatsP1,
    importStatsP2,
    jaarVan,
    jaarTot,
    resultaat,
    inputSignatureAtCalculation,
    state.activeStep,
    activeHouseholdName,
    activeScenarioName,
    state.calculationStatus,
    actions,
  ]);

  useEffect(() => {
    if (resultaat && inputSignatureAtCalculation && inputSignature !== inputSignatureAtCalculation) {
      actions.markStale();
    }
  }, [resultaat, inputSignatureAtCalculation, inputSignature, actions]);

  useEffect(() => {
    actions.setContext({ currentHousehold: activeHouseholdName });
  }, [activeHouseholdName, actions]);

  useEffect(() => {
    if (scenarios.length === 0) {
      const fallback = [{ id: crypto.randomUUID(), naam: "Basisscenario" }];
      const fallbackData = createDefaultScenarioData();
      setScenarios(fallback);
      setScenarioSnapshots({ [fallback[0].id]: fallbackData });
      setActiveScenarioId(fallback[0].id);
      hydrateFromScenarioSnapshot(fallbackData);
      return;
    }

    const hasActive = activeScenarioId && scenarios.some((scenario) => scenario.id === activeScenarioId);
    if (!hasActive) {
      const nextId = scenarios[0].id;
      setActiveScenarioId(nextId);
      const nextData = scenarioSnapshots[nextId] || createDefaultScenarioData();
      hydrateFromScenarioSnapshot(nextData);
    }
  }, [scenarios, activeScenarioId, scenarioSnapshots]);

  useEffect(() => {
    actions.setContext({ activeScenario: activeScenarioName });
  }, [activeScenarioName, actions]);

  useEffect(() => {
    const availableScenarioIds = scenarios.map((scenario) => scenario.id).filter((id) => id !== activeScenarioId);
    if (availableScenarioIds.length === 0) {
      if (compareScenarioId) {
        setCompareScenarioId("");
      }
      return;
    }

    if (!compareScenarioId || !availableScenarioIds.includes(compareScenarioId)) {
      setCompareScenarioId(availableScenarioIds[0]);
    }
  }, [scenarios, activeScenarioId, compareScenarioId]);

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    const nextSnapshot = buildCurrentSnapshot();
    setHouseholdSnapshots((prev) => {
      const previous = prev[activeHouseholdId];
      if (JSON.stringify(previous) === JSON.stringify(nextSnapshot)) {
        return prev;
      }
      return {
        ...prev,
        [activeHouseholdId]: nextSnapshot,
      };
    });
  }, [
    hydrated,
    activeHouseholdId,
    posts,
    apiBase,
    persoonNaam,
    geboortedatum,
    heeftPartner,
    partnerNaam,
    partnerGeboortedatum,
    scenarios,
    activeScenarioId,
    scenarioSnapshots,
    compareScenarioId,
    comparisonResult,
    importBestandP1Naam,
    importBestandP2Naam,
    importPreviewP1,
    importPreviewP2,
    importWarningsP1,
    importWarningsP2,
    importStatsP1,
    importStatsP2,
    jaarVan,
    jaarTot,
    resultaat,
    inputSignatureAtCalculation,
    state.calculationStatus,
  ]);

  const currentStepIndex = FLOW_STEPS.findIndex((step) => step.id === activeStep);
  const stepCompletion = {
    huishouden: Boolean(activeHouseholdName && activeHouseholdName.trim()),
    personen: personenIsValid,
    import: Boolean(importBestandP1Naam || (!heeftPartner || importBestandP2Naam)),
    periode: periodeIsValid,
    scenario: Boolean(activeScenarioName && activeScenarioName.trim()),
    componenten: posts.length > 0,
    resultaten: Boolean(resultaat),
    accountant: Boolean(resultaat),
    rapport: Boolean(resultaat),
  };

  const canCalculate = stepCompletion.huishouden && personenIsValid && periodeIsValid;

  const createBerekeningPayload = () =>
    buildRequestPayload({
      posts,
      persoonNaam,
      geboortedatum,
      jaarVan,
      jaarTot,
      scenarioNaam: activeScenarioName,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
    });

  const stepStatusMap = FLOW_STEPS.reduce((acc, step) => {
    if (step.id === activeStep) {
      acc[step.id] = "active";
      return acc;
    }
    if (step.id === "resultaten" && state.calculationStatus === "stale") {
      acc[step.id] = "stale";
      return acc;
    }
    acc[step.id] = stepCompletion[step.id] ? "completed" : "pending";
    return acc;
  }, {});

  const runBerekening = async () => {
    if (!canCalculate) {
      if (!personenIsValid) {
        actions.setActiveStep("personen");
        setErrorMessage("Vul eerst geldige persoonsgegevens in (inclusief partner indien actief).");
      } else if (!periodeIsValid) {
        actions.setActiveStep("periode");
        setErrorMessage("Corrigeer eerst de berekeningsperiode.");
      } else {
        setErrorMessage("Corrigeer eerst de invoer voordat je berekent.");
      }
      return;
    }

    setIsLoading(true);
    setErrorMessage("");
    actions.setCalcStatus("calculating");
    try {
      const payload = createBerekeningPayload();
      const response = await fetch(`${apiBase}/berekeningen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = data?.detail;
        if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
          setErrorMessage(detail[0].msg);
        } else if (typeof detail === "string") {
          setErrorMessage(detail);
        } else if (detail?.message) {
          setErrorMessage(detail.message);
        } else {
          setErrorMessage(`API fout (${response.status})`);
        }
        actions.setCalcStatus(resultaat ? "stale" : "idle");
        return;
      }

      setResultaat(data);
      setInputSignatureAtCalculation(inputSignature);
      actions.markFresh();
      actions.setActiveStep("resultaten");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Onbekende fout bij berekening");
      actions.setCalcStatus(resultaat ? "stale" : "idle");
    } finally {
      setIsLoading(false);
    }
  };

  const downloadRapport = async () => {
    if (!canCalculate) {
      if (!personenIsValid) {
        actions.setActiveStep("personen");
        setReportErrorMessage("Vul eerst geldige persoonsgegevens in (inclusief partner indien actief).");
      } else if (!periodeIsValid) {
        actions.setActiveStep("periode");
        setReportErrorMessage("Corrigeer eerst de berekeningsperiode.");
      } else {
        setReportErrorMessage("Corrigeer eerst de invoer voordat je een rapport downloadt.");
      }
      return;
    }

    setIsReportLoading(true);
    setReportErrorMessage("");

    try {
      const response = await fetch(`${apiBase}/rapportages/excel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          berekening: createBerekeningPayload(),
          include_vergelijking: false,
          scenarios_vergelijking: [],
        }),
      });

      if (!response.ok) {
        let detailMessage = `Rapportage mislukt (${response.status})`;
        try {
          const data = await response.json();
          const detail = data?.detail;
          if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
            detailMessage = detail[0].msg;
          } else if (typeof detail === "string") {
            detailMessage = detail;
          } else if (detail?.message) {
            detailMessage = detail.message;
          }
        } catch {
          // Keep fallback message when body is not JSON.
        }
        setReportErrorMessage(detailMessage);
        return;
      }

      const blob = await response.blob();
      const contentDisposition = response.headers.get("content-disposition");
      const filename = extractFilename(contentDisposition);

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setReportErrorMessage(err instanceof Error ? err.message : "Onbekende fout bij rapportage");
    } finally {
      setIsReportLoading(false);
    }
  };

  const renderResultaten = () => (
    <ResultsSection SectionHeader={SectionHeader} jaarRows={jaarRows} euro={euro} />
  );

  const renderStepContent = () => {
    if (activeStep === "huishouden") {
      return (
        <section className="section">
          <SectionHeader title="Huishouden" description="Beheer meerdere huishoudens en schakel tussen hun eigen invoersessies." />
          <div className="household-controls">
            <label className="field inline-field">
              <span>Actief huishouden</span>
              <select value={activeHouseholdId} onChange={(e) => switchHousehold(e.target.value)}>
                {households.map((household) => (
                  <option key={household.id} value={household.id}>
                    {household.name || "Onbenoemd huishouden"}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="ghost" onClick={removeActiveHousehold} disabled={households.length <= 1}>
              Verwijder actief huishouden
            </button>
          </div>

          <label className="field inline-field">
            <span>Huishouden naam</span>
            <input value={activeHouseholdName} onChange={(e) => renameActiveHousehold(e.target.value)} />
          </label>

          <div className="household-controls">
            <label className="field inline-field">
              <span>Nieuw huishouden</span>
              <input
                value={newHouseholdName}
                placeholder="Bijv. Scenario met verhuizing"
                onChange={(e) => setNewHouseholdName(e.target.value)}
              />
            </label>
            <button type="button" onClick={addHousehold}>Huishouden toevoegen</button>
          </div>
        </section>
      );
    }

    if (activeStep === "personen") {
      return (
        <>
          <header className="hero compact">
            <p className="eyebrow">Personen</p>
            <h1>Huishoudgegevens</h1>
            <p>Leg de basis vast voor persoon en API-verbinding.</p>
            <div className="toolbar">
              <label className="field"><span>API basis</span><input value={apiBase} onChange={(e) => setApiBase(e.target.value)} /></label>
              <label className="field"><span>P1 naam</span><input value={persoonNaam} onChange={(e) => setPersoonNaam(e.target.value)} /></label>
              <label className="field"><span>P1 geboortedatum</span><input type="date" value={geboortedatum} onChange={(e) => setGeboortedatum(e.target.value)} /></label>
            </div>

            <div className="toolbar">
              <label className="field inline-toggle">
                <span>Partner (P2) meenemen</span>
                <input
                  type="checkbox"
                  checked={heeftPartner}
                  onChange={(e) => {
                    const enabled = e.target.checked;
                    setHeeftPartner(enabled);
                    if (!enabled) {
                      setPartnerNaam("");
                      setPartnerGeboortedatum("");
                    }
                  }}
                />
              </label>
              <label className="field"><span>P2 naam</span><input value={partnerNaam} disabled={!heeftPartner} onChange={(e) => setPartnerNaam(e.target.value)} /></label>
              <label className="field"><span>P2 geboortedatum</span><input type="date" value={partnerGeboortedatum} disabled={!heeftPartner} onChange={(e) => setPartnerGeboortedatum(e.target.value)} /></label>
            </div>

            {!personenIsValid ? (
              <p className="notice warning">Vul alle verplichte velden voor P1 en optioneel P2 volledig in.</p>
            ) : null}
            {errorMessage ? <p className="error">{errorMessage}</p> : null}
          </header>
        </>
      );
    }

    if (activeStep === "periode") {
      return (
        <section className="section">
          <SectionHeader title="Berekeningsperiode" description="Stel globale periode in. Componenten kunnen later een eigen looptijd hebben." />
          <div className="toolbar">
            <label className="field"><span>Jaar van</span><input type="number" value={jaarVan} onChange={(e) => setJaarVan(e.target.value)} /></label>
            <label className="field"><span>Jaar tot</span><input type="number" value={jaarTot} onChange={(e) => setJaarTot(e.target.value)} /></label>
          </div>
          {periodeValidatie.length > 0 ? (
            <ul className="validation-list">
              {periodeValidatie.map((melding) => (
                <li key={melding}>{melding}</li>
              ))}
            </ul>
          ) : (
            <p className="notice">Periode is geldig.</p>
          )}
        </section>
      );
    }

    if (activeStep === "scenario") {
      return (
        <ScenarioSection
          SectionHeader={SectionHeader}
          activeScenario={activeScenario}
          activeScenarioId={activeScenarioId}
          activeScenarioName={activeScenarioName}
          scenarios={scenarios}
          newScenarioName={newScenarioName}
          setNewScenarioName={setNewScenarioName}
          switchScenario={switchScenario}
          removeActiveScenario={removeActiveScenario}
          renameActiveScenario={renameActiveScenario}
          addScenario={addScenario}
          duplicateActiveScenario={duplicateActiveScenario}
          compareScenarioId={compareScenarioId}
          setCompareScenarioId={setCompareScenarioId}
          runScenarioComparison={runScenarioComparison}
          isComparing={isComparing}
          comparisonError={comparisonError}
          comparisonResult={comparisonResult}
          comparisonSummary={comparisonSummary}
          compareScenarioName={compareScenarioName}
          signedEuro={signedEuro}
          signedPercentagePoints={signedPercentagePoints}
          euro={euro}
          decimalLike={decimalLike}
        />
      );
    }

    if (activeStep === "componenten") {
      return (
        <ComponentsSection
          SectionHeader={SectionHeader}
          NewPostPicker={NewPostPicker}
          PostCard={PostCard}
          typeConfig={TYPE_CONFIG}
          fieldMeta={FIELD_META}
          inkomstenTypes={inkomstenTypes}
          inkomenType={inkomenType}
          setInkomenType={setInkomenType}
          addPost={addPost}
          inkomstenPosts={inkomstenPosts}
          updatePost={updatePost}
          removePost={removePost}
          vermogenTypes={vermogenTypes}
          vermogenType={vermogenType}
          setVermogenType={setVermogenType}
          vermogenPosts={vermogenPosts}
          payloadPreview={payloadPreview}
        />
      );
    }

    if (activeStep === "resultaten") {
      return renderResultaten();
    }

    if (activeStep === "accountant") {
      return (
        <AccountantSection SectionHeader={SectionHeader} resultsSection={renderResultaten()} />
      );
    }

    if (activeStep === "rapport") {
      return (
        <ReportSection
          SectionHeader={SectionHeader}
          downloadRapport={downloadRapport}
          isReportLoading={isReportLoading}
          canCalculate={canCalculate}
          reportErrorMessage={reportErrorMessage}
        />
      );
    }

    if (activeStep === "import") {
      return (
        <MpoImportSection
          heeftPartner={heeftPartner}
          isImportingP1={isImportingP1}
          isImportingP2={isImportingP2}
          importBestandP1Naam={importBestandP1Naam}
          importBestandP2Naam={importBestandP2Naam}
          importPreviewP1={importPreviewP1}
          importPreviewP2={importPreviewP2}
          importStatsP1={importStatsP1}
          importStatsP2={importStatsP2}
          importWarningsP1={importWarningsP1}
          importWarningsP2={importWarningsP2}
          importInfoMessages={importInfoMessages}
          importErrorMessages={importErrorMessages}
          onImportFile={importMpoFileForPersoon}
          SectionHeader={SectionHeader}
        />
      );
    }

    return null;
  };

  const gotoPreviousStep = () => {
    if (currentStepIndex > 0) {
      actions.setActiveStep(FLOW_STEPS[currentStepIndex - 1].id);
    }
  };

  const gotoNextStep = () => {
    if (currentStepIndex < FLOW_STEPS.length - 1) {
      actions.setActiveStep(FLOW_STEPS[currentStepIndex + 1].id);
    }
  };

  return (
    <AppShell
      sidebar={<WizardSidebar steps={FLOW_STEPS} activeStep={activeStep} stepStatusMap={stepStatusMap} onStepSelect={actions.setActiveStep} calculationStatus={state.calculationStatus} isCalculating={isLoading} />}
      topbar={<ContextTopBar currentHousehold={activeHouseholdName} activeScenario={activeScenarioName} calculationStatus={state.calculationStatus} lastCalculatedAt={state.lastCalculatedAt} autosaveStatus={state.autosaveStatus} onCalculate={runBerekening} isCalculating={isLoading} canCalculate={canCalculate} />}
      footer={
        <div className="flow-nav">
          <button type="button" onClick={gotoPreviousStep} disabled={currentStepIndex <= 0}>Vorige</button>
          <button type="button" onClick={gotoNextStep} disabled={currentStepIndex >= FLOW_STEPS.length - 1}>Volgende</button>
        </div>
      }
    >
      {renderStepContent()}
    </AppShell>
  );
}

export default function App() {
  return (
    <AppStateProvider>
      <AppContent />
    </AppStateProvider>
  );
}
