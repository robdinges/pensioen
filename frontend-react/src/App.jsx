import { useEffect, useMemo, useState } from "react";
import { compactSession, saveSession } from "./planner/sessionStorage";
import AccountantSection from "./components/AccountantSection";
import AppShell from "./components/layout/AppShell";
import ComponentsSection from "./components/ComponentsSection";
import ContextTopBar from "./components/layout/ContextTopBar";
import {
  selectYearRows,
  validateCalculationResponse,
  buildRequestPayload,
  buildInputSignature,
  createEmptyValues,
  createDefaultScenarioData,
  createHouseholdPreferences,
  createHouseholdSnapshot,
  createInitialHouseholdSnapshot,
  createPost,
  decimalLike,
  DEFAULT_API_BASE,
  DEFAULT_GEBOORTEDATUM,
  DEFAULT_PERSOON_NAAM,
  euro,
  extractFilename,
  FIELD_META,
  FLOW_STEPS,
  normalizeHouseholdSnapshot,
  normalizeHouseholdPreferences,
  normalizeScenarioSnapshot,
  createScenarioSnapshot,
  signedEuro,
  signedPercentagePoints,
  TYPE_CONFIG,
} from "./planner/plannerCore";
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
  const [componentLayout, setComponentLayout] = useState("masterpiece");
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [persoonNaam, setPersoonNaam] = useState(DEFAULT_PERSOON_NAAM);
  const [geboortedatum, setGeboortedatum] = useState(DEFAULT_GEBOORTEDATUM);
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
  const [pendingImports, setPendingImports] = useState({ P1: null, P2: null });
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
    [initialHouseholdId]: createInitialHouseholdSnapshot({
      scenarioId: initialScenarioId,
      scenarioNaam: "Basisscenario",
      scenarioData: createDefaultScenarioData(),
      persoonNaam: DEFAULT_PERSOON_NAAM,
      geboortedatum: DEFAULT_GEBOORTEDATUM,
    }),
  });
  const [householdPreferences, setHouseholdPreferences] = useState({
    [initialHouseholdId]: createHouseholdPreferences(),
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

  const buildCurrentScenarioSnapshot = () =>
    createScenarioSnapshot({
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
      jaarVan,
      jaarTot,
      scenarioNaam,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
    });
    return request;
  };

  const hydrateFromScenarioSnapshot = (snapshot, { includePeriod = false } = {}) => {
    const source = normalizeScenarioSnapshot(snapshot);
    setPosts(source.posts);
    if (includePeriod) {
      setJaarVan(source.jaarVan);
      setJaarTot(source.jaarTot);
    }
    setImportBestandP1Naam(source.importBestandP1Naam);
    setImportBestandP2Naam(source.importBestandP2Naam);
    setImportPreviewP1(source.importPreviewP1);
    setImportPreviewP2(source.importPreviewP2);
    setImportWarningsP1(source.importWarningsP1);
    setImportWarningsP2(source.importWarningsP2);
    setImportStatsP1(source.importStatsP1);
    setImportStatsP2(source.importStatsP2);
    setResultaat(source.resultaat || null);
    setInputSignatureAtCalculation(source.inputSignatureAtCalculation);
    actions.setCalcStatus(source.calculationStatus);
  };

  const buildCurrentPreferences = () =>
    createHouseholdPreferences({ jaarVan, jaarTot, apiBase, inkomenType, vermogenType });

  const applyHouseholdPreferences = (preferences, fallback = {}) => {
    const source = normalizeHouseholdPreferences(preferences, fallback);
    setJaarVan(source.jaarVan);
    setJaarTot(source.jaarTot);
    setApiBase(source.apiBase);
    setInkomenType(source.inkomenType);
    setVermogenType(source.vermogenType);
  };

  const updateHouseholdPreference = (key, value) => {
    const setters = {
      jaarVan: setJaarVan,
      jaarTot: setJaarTot,
      apiBase: setApiBase,
      inkomenType: setInkomenType,
      vermogenType: setVermogenType,
    };
    setters[key](value);
    setHouseholdPreferences((prev) => ({
      ...prev,
      [activeHouseholdId]: {
        ...normalizeHouseholdPreferences(prev[activeHouseholdId]),
        [key]: value,
      },
    }));
  };

  const buildCurrentSnapshot = () => {
    const currentScenarioSnapshots = {
      ...scenarioSnapshots,
      [activeScenarioId]: buildCurrentScenarioSnapshot(),
    };
    return createHouseholdSnapshot({
      posts,
      apiBase,
      persoonNaam,
      geboortedatum,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
      scenarios,
      activeScenarioId,
      scenarioSnapshots: currentScenarioSnapshots,
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
  };

  const hydrateFromSnapshot = (snapshot) => {
    const source = normalizeHouseholdSnapshot(snapshot);
    setPosts(source.posts);
    setApiBase(source.apiBase);
    setPersoonNaam(source.persoonNaam);
    setGeboortedatum(source.geboortedatum);
    setHeeftPartner(source.heeftPartner);
    setPartnerNaam(source.partnerNaam);
    setPartnerGeboortedatum(source.partnerGeboortedatum);
    setJaarVan(source.jaarVan);
    setJaarTot(source.jaarTot);
    setScenarios(source.scenarios);
    setActiveScenarioId(source.activeScenarioId);
    setScenarioSnapshots(source.scenarioSnapshots);
    setCompareScenarioId(source.compareScenarioId);
    setComparisonResult(source.comparisonResult);
    hydrateFromScenarioSnapshot(source.activeScenarioSnapshot);
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
    const updatedPreferences = {
      ...householdPreferences,
      [activeHouseholdId]: buildCurrentPreferences(),
    };

    setHouseholdSnapshots(updatedSnapshots);
    setPendingImports({ P1: null, P2: null });
    setHouseholdPreferences(updatedPreferences);
    setActiveHouseholdId(nextHouseholdId);
    hydrateFromSnapshot(nextSnapshot);
    applyHouseholdPreferences(updatedPreferences[nextHouseholdId], nextSnapshot);
  };

  const addHousehold = () => {
    const label = newHouseholdName.trim() || `Huishouden ${households.length + 1}`;
    const nextHouseholdId = crypto.randomUUID();
    const snapshot = createInitialHouseholdSnapshot({ scenarioNaam: "Basisscenario" });

    setHouseholds((prev) => [...prev, { id: nextHouseholdId, name: label }]);
    setPendingImports({ P1: null, P2: null });
    setHouseholdSnapshots((prev) => ({
      ...prev,
      [activeHouseholdId]: buildCurrentSnapshot(),
      [nextHouseholdId]: snapshot,
    }));
    setHouseholdPreferences((prev) => ({
      ...prev,
      [activeHouseholdId]: buildCurrentPreferences(),
      [nextHouseholdId]: createHouseholdPreferences(snapshot),
    }));
    setActiveHouseholdId(nextHouseholdId);
    setNewHouseholdName("");
    hydrateFromSnapshot(snapshot);
    applyHouseholdPreferences(createHouseholdPreferences(snapshot));
  };

  const removeActiveHousehold = () => {
    if (households.length <= 1) {
      return;
    }

    const remaining = households.filter((household) => household.id !== activeHouseholdId);
    const nextActiveId = remaining[0].id;
    const nextSnapshot = householdSnapshots[nextActiveId] || null;

    setHouseholds(remaining);
    setPendingImports({ P1: null, P2: null });
    setHouseholdSnapshots((prev) => {
      const clone = { ...prev };
      delete clone[activeHouseholdId];
      return clone;
    });
    setHouseholdPreferences((prev) => {
      const clone = { ...prev };
      delete clone[activeHouseholdId];
      return clone;
    });
    setActiveHouseholdId(nextActiveId);
    hydrateFromSnapshot(nextSnapshot);
    applyHouseholdPreferences(householdPreferences[nextActiveId], nextSnapshot);
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
    setPendingImports({ P1: null, P2: null });
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
    setPendingImports({ P1: null, P2: null });
    setActiveScenarioId(nextScenarioId);
    hydrateFromScenarioSnapshot(targetSnapshot);
  };

  const removeActiveScenario = () => {
    if (scenarios.length <= 1) {
      return;
    }
    const remaining = scenarios.filter((scenario) => scenario.id !== activeScenarioId);
    setPendingImports({ P1: null, P2: null });
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
      const jaarVanVergelijking = Number(jaarVan);
      const jaarTotVergelijking = Number(jaarTot);

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
        rows = parseJsonText(content, {
          geboortedatum: persoonCode === "P2" ? partnerGeboortedatum : geboortedatum,
        });
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
          ...createEmptyValues("pensioen"),
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

      if (persoonCode === "P1") {
        setImportPreviewP1(preview);
        setImportWarningsP1(analyse.warnings);
        setImportStatsP1(analyse.stats);
      } else {
        setImportPreviewP2(preview);
        setImportWarningsP2(analyse.warnings);
        setImportStatsP2(analyse.stats);
      }

      if (importedPosts.length === 0) {
        setPendingImports((prev) => ({ ...prev, [persoonCode]: null }));
        setImportInfoFor(persoonCode, `Geen bruikbare pensioenregels gevonden in ${file.name}.`);
        return;
      }

      setPendingImports((prev) => ({
        ...prev,
        [persoonCode]: { fileName: file.name, posts: importedPosts },
      }));
      setImportInfoFor(
        persoonCode,
        `Controleer de preview. Er wordt nog niets toegevoegd totdat je bevestigt.`,
      );
    } catch (err) {
      setImportInfoFor(persoonCode, "");
      setImportErrorFor(persoonCode, err instanceof Error ? err.message : "Onbekende fout bij import.");
    } finally {
      setImportingFor(persoonCode, false);
    }
  };

  const confirmMpoImport = (persoonCode) => {
    const pending = pendingImports[persoonCode];
    if (!pending) {
      return;
    }
    setPosts((prev) => {
      const withoutOldMpoForPerson = prev.filter(
        (post) => !(post.type === "pensioen" && post.source === "mpo" && post.values?.persoon === persoonCode),
      );
      return [...withoutOldMpoForPerson, ...pending.posts];
    });
    if (persoonCode === "P1") {
      setImportBestandP1Naam(pending.fileName);
    } else {
      setImportBestandP2Naam(pending.fileName);
    }
    setPendingImports((prev) => ({ ...prev, [persoonCode]: null }));
    setImportInfoFor(
      persoonCode,
      `${pending.posts.length} pensioenregel(s) toegevoegd voor ${persoonCode}.`,
    );
    setErrorMessage("");
  };

  const cancelMpoImport = (persoonCode) => {
    setPendingImports((prev) => ({ ...prev, [persoonCode]: null }));
    setImportInfoFor(persoonCode, "Import geannuleerd; er zijn geen componenten gewijzigd.");
  };

  const payloadPreview = {
    inkomsten_uitgaven: inkomstenPosts.map((post) => ({ id: post.id, type: post.type, titel: post.titel, ...post.values })),
    vermogen: vermogenPosts.map((post) => ({ id: post.id, type: post.type, titel: post.titel, ...post.values })),
  };

  const jaarRows = useMemo(() => selectYearRows(resultaat?.cashflow), [resultaat]);
  const calculationInputSignature = useMemo(
    () =>
      buildInputSignature(
        createBerekeningPayload(),
      ),
    [
      posts,
      persoonNaam,
      geboortedatum,
      jaarVan,
      jaarTot,
      activeScenarioName,
      heeftPartner,
      partnerNaam,
      partnerGeboortedatum,
    ],
  );

  useEffect(() => {
    if (hydrated) return; // Bewaar actuele invoer bij hot reload; hydrateer alleen bij openen.
    try {
      const raw = localStorage.getItem("pensioen-ui-session-v1");
      if (raw) {
        const parsed = JSON.parse(raw);

        const parsedHouseholds = Array.isArray(parsed.households) ? parsed.households : null;
        const parsedSnapshots = parsed.householdSnapshots && typeof parsed.householdSnapshots === "object"
          ? parsed.householdSnapshots
          : null;

        if (parsedHouseholds && parsedHouseholds.length > 0 && parsedSnapshots) {
          const parsedPreferences =
            parsed.householdPreferences && typeof parsed.householdPreferences === "object"
              ? parsed.householdPreferences
              : {};
          const migratedPreferences = Object.fromEntries(
            parsedHouseholds.map((household) => [
              household.id,
              normalizeHouseholdPreferences(
                parsedPreferences[household.id],
                parsedSnapshots[household.id],
              ),
            ]),
          );
          setHouseholds(parsedHouseholds);
          setHouseholdSnapshots(parsedSnapshots);
          setHouseholdPreferences(migratedPreferences);
          const persistedActiveId =
            typeof parsed.activeHouseholdId === "string" &&
            parsedHouseholds.some((item) => item.id === parsed.activeHouseholdId)
              ? parsed.activeHouseholdId
              : parsedHouseholds[0].id;
          setActiveHouseholdId(persistedActiveId);
          hydrateFromSnapshot(parsedSnapshots[persistedActiveId]);
          applyHouseholdPreferences(
            migratedPreferences[persistedActiveId],
            parsedSnapshots[persistedActiveId],
          );
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

  const buildSessionPayload = () => ({
    households,
    activeHouseholdId,
    householdSnapshots: {
      ...householdSnapshots,
      [activeHouseholdId]: buildCurrentSnapshot(),
    },
    householdPreferences: {
      ...householdPreferences,
      [activeHouseholdId]: buildCurrentPreferences(),
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
  });

  const retrySaveSession = () => {
    try {
      saveSession(buildSessionPayload());
      actions.setAutosaveStatus("saved");
    } catch {
      actions.setAutosaveStatus("error");
    }
  };

  const downloadInputBackup = () => {
    const content = JSON.stringify(compactSession(buildSessionPayload()), null, 2);
    const url = URL.createObjectURL(new Blob([content], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "pensioen-invoer-backup.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  useEffect(() => {
    if (!hydrated) {
      return;
    }

    actions.setAutosaveStatus("saving");
    const payload = buildSessionPayload();
    try {
      saveSession(payload);
    } catch {
      actions.setAutosaveStatus("error");
      return;
    }

    const timer = setTimeout(() => actions.setAutosaveStatus("saved"), 250);
    return () => clearTimeout(timer);
  }, [
    hydrated,
    households,
    activeHouseholdId,
    householdSnapshots,
    householdPreferences,
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
    if (resultaat && inputSignatureAtCalculation && calculationInputSignature !== inputSignatureAtCalculation) {
      actions.markStale();
    }
  }, [resultaat, inputSignatureAtCalculation, calculationInputSignature, actions]);

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
    import: Boolean(importBestandP1Naam && (!heeftPartner || importBestandP2Naam)),
    periode: periodeIsValid,
    scenario: Boolean(activeScenarioName && activeScenarioName.trim()),
    componenten: posts.length > 0,
    resultaten: Boolean(resultaat),
    accountant: Boolean(resultaat),
    rapport: Boolean(resultaat),
  };

  const canCalculate = stepCompletion.huishouden && personenIsValid && periodeIsValid;

  function createBerekeningPayload() {
    return buildRequestPayload({
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
  }

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
      const requestSignature = buildInputSignature(payload);
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

      setResultaat(validateCalculationResponse(data));
      setInputSignatureAtCalculation(requestSignature);
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
    <ResultsSection
      SectionHeader={SectionHeader} jaarRows={jaarRows} euro={euro}
      aannames={resultaat?.aannames || []}
      calculationStatus={state.calculationStatus}
      onStepSelect={actions.setActiveStep}
    />
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
                placeholder="Bijv. Familie De Vries"
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
            <p>Voor wie maak je een pensioenplan? Je geboortedatum is nodig om je AOW-start te bepalen.</p>
            <div className="toolbar">
              <label className="field"><span>Je naam</span><input value={persoonNaam} onChange={(e) => setPersoonNaam(e.target.value)} /></label>
              <label className="field"><span>Je geboortedatum</span><input type="date" value={geboortedatum} onChange={(e) => setGeboortedatum(e.target.value)} /></label>
            </div>

            <div className="toolbar">
              <label className="field inline-toggle">
                <span>Samen met een partner plannen</span>
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
              <label className="field"><span>Naam partner</span><input value={partnerNaam} disabled={!heeftPartner} onChange={(e) => setPartnerNaam(e.target.value)} /></label>
              <label className="field"><span>Geboortedatum partner</span><input type="date" value={partnerGeboortedatum} disabled={!heeftPartner} onChange={(e) => setPartnerGeboortedatum(e.target.value)} /></label>
            </div>

            {!personenIsValid ? (
              <p className="notice warning">Vul je naam en een geldige geboortedatum in. Doe dit ook voor je partner als je samen plant.</p>
            ) : null}
            <details className="connection-settings">
              <summary>Verbindingsinstellingen</summary>
              <label className="field"><span>Adres rekenservice</span><input value={apiBase} onChange={(e) => updateHouseholdPreference("apiBase", e.target.value)} /></label>
            </details>
          </header>
        </>
      );
    }

    if (activeStep === "periode") {
      return (
        <section className="section">
          <SectionHeader title="Berekeningsperiode" description="Stel globale periode in. Componenten kunnen later een eigen looptijd hebben." />
          <div className="toolbar">
            <label className="field"><span>Jaar van</span><input type="number" value={jaarVan} onChange={(e) => updateHouseholdPreference("jaarVan", e.target.value)} /></label>
            <label className="field"><span>Jaar tot</span><input type="number" value={jaarTot} onChange={(e) => updateHouseholdPreference("jaarTot", e.target.value)} /></label>
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
          setInkomenType={(value) => updateHouseholdPreference("inkomenType", value)}
          addPost={addPost}
          inkomstenPosts={inkomstenPosts}
          updatePost={updatePost}
          removePost={removePost}
          vermogenTypes={vermogenTypes}
          vermogenType={vermogenType}
          setVermogenType={(value) => updateHouseholdPreference("vermogenType", value)}
          vermogenPosts={vermogenPosts}
          payloadPreview={payloadPreview}
          layoutVariant={componentLayout}
          setLayoutVariant={setComponentLayout}
        />
      );
    }

    if (activeStep === "resultaten") {
      return renderResultaten();
    }

    if (activeStep === "accountant") {
      return (
        <AccountantSection SectionHeader={SectionHeader} resultaat={resultaat} euro={euro} posts={posts} />
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
          pendingImports={pendingImports}
          onImportFile={importMpoFileForPersoon}
          onConfirmImport={confirmMpoImport}
          onCancelImport={cancelMpoImport}
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
      className={activeStep === "componenten" ? `component-layout-${componentLayout}` : ""}
      sidebar={<WizardSidebar steps={FLOW_STEPS} activeStep={activeStep} stepStatusMap={stepStatusMap} onStepSelect={actions.setActiveStep} calculationStatus={state.calculationStatus} isCalculating={isLoading} />}
      topbar={<ContextTopBar currentHousehold={activeHouseholdName} activeScenario={activeScenarioName} calculationStatus={state.calculationStatus} lastCalculatedAt={state.lastCalculatedAt} autosaveStatus={state.autosaveStatus} onCalculate={runBerekening} isCalculating={isLoading} canCalculate={canCalculate} />}
      footer={
        <div className="flow-nav">
          <button type="button" className="ghost" onClick={gotoPreviousStep} disabled={currentStepIndex <= 0}>Terug</button>
          <span className="flow-position">Stap {currentStepIndex + 1} van {FLOW_STEPS.length}</span>
          <button type="button" onClick={gotoNextStep} disabled={currentStepIndex >= FLOW_STEPS.length - 1}>
            {currentStepIndex < FLOW_STEPS.length - 1 ? `Verder: ${FLOW_STEPS[currentStepIndex + 1].label}` : "Laatste stap"}
          </button>
        </div>
      }
    >
      {errorMessage ? <p className="feedback-banner error" role="alert">{errorMessage}</p> : null}
      {state.autosaveStatus === "error" ? (
        <div className="feedback-banner error" role="alert">
          <p>Je invoer kon niet worden opgeslagen. De browseropslag kan vol of geblokkeerd zijn. Houd dit tabblad open en download je invoer voordat je herlaadt.</p>
          <button type="button" onClick={downloadInputBackup}>Download back-up van mijn invoer</button>{" "}
          <button type="button" onClick={retrySaveSession}>Opnieuw opslaan</button>
        </div>
      ) : null}
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
