import { useMemo, useState } from "react";

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

function buildRequestPayload({ posts, persoonNaam, geboortedatum, jaarVan, jaarTot }) {
  const inkomstenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "inkomsten");
  const vermogenPosts = posts.filter((post) => TYPE_CONFIG[post.type].section === "vermogen");

  const componenten = [];
  const incidentele_items = [];
  const vermogensitems = [];

  let jaarlijkse_inleg_sparen = 0;
  let jaarlijkse_inleg_beleggen = 0;
  let spaargeld_start = 0;
  let beleggingen_start = 0;
  const sparen_rendementen = [];
  const beleggen_rendementen = [];

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
      persoon: values.persoon || "P1",
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
      sparen_rendementen.push(toAmount(values.groei_pct));
    }
    if (post.type === "beleggen") {
      beleggingen_start += Math.max(0, toAmount(values.beginwaarde));
      jaarlijkse_inleg_beleggen += Math.max(0, toAmount(values.inleg));
      beleggen_rendementen.push(toAmount(values.groei_pct));
    }

    const item = {
      omschrijving: post.titel,
      type,
      persoon: values.persoon || "Huishouden",
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
    sparen_rendementen.length > 0
      ? sparen_rendementen.reduce((sum, value) => sum + value, 0) / sparen_rendementen.length
      : 0;
  const rendement_beleggen_pct =
    beleggen_rendementen.length > 0
      ? beleggen_rendementen.reduce((sum, value) => sum + value, 0) / beleggen_rendementen.length
      : 0;

  return {
    scenario: {
      naam: "React UI scenario",
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
      heeft_partner: false,
    },
    persoon2: null,
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

    const vermogenEinde = maanden.length
      ? toAmount(maanden[maanden.length - 1].vermogen_einde_maand)
      : 0;

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

function PostCard({ post, onChange, onDelete }) {
  const config = TYPE_CONFIG[post.type];

  return (
    <article className="card">
      <div className="card-top">
        <div>
          <h3>{config.label}</h3>
          <p>{config.hint}</p>
        </div>
        <button className="ghost" onClick={() => onDelete(post.id)}>
          Verwijder
        </button>
      </div>

      <label className="field">
        <span>Titel</span>
        <input
          type="text"
          value={post.titel}
          onChange={(e) => onChange(post.id, "titel", e.target.value, true)}
        />
      </label>

      <div className="grid">
        {config.fields.map((field) => {
          const meta = FIELD_META[field];
          const value = post.values[field] ?? "";

          if (meta.type === "select") {
            return (
              <label key={field} className="field">
                <span>{meta.label}</span>
                <select value={value} onChange={(e) => onChange(post.id, field, e.target.value)}>
                  {meta.options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            );
          }

          return (
            <label key={field} className="field">
              <span>{meta.label}</span>
              <input
                type={meta.type}
                value={value}
                step={meta.step}
                onChange={(e) => onChange(post.id, field, e.target.value)}
              />
            </label>
          );
        })}
      </div>
    </article>
  );
}

function NewPostPicker({ title, options, value, onValueChange, onAdd }) {
  return (
    <div className="add-row">
      <h4>{title}</h4>
      <div>
        <select value={value} onChange={(e) => onValueChange(e.target.value)}>
          {options.map((option) => (
            <option key={option} value={option}>
              {TYPE_CONFIG[option].label}
            </option>
          ))}
        </select>
        <button onClick={onAdd}>+ Post toevoegen</button>
      </div>
    </div>
  );
}

export default function App() {
  const [posts, setPosts] = useState([createPost("loon"), createPost("sparen")]);
  const [inkomenType, setInkomenType] = useState("uitkering");
  const [vermogenType, setVermogenType] = useState("beleggen");
  const [apiBase, setApiBase] = useState("/api/v1");
  const [persoonNaam, setPersoonNaam] = useState("Jan Jansen");
  const [geboortedatum, setGeboortedatum] = useState("1963-03-15");
  const [jaarVan, setJaarVan] = useState(String(new Date().getFullYear()));
  const [jaarTot, setJaarTot] = useState(String(new Date().getFullYear() + 20));
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [resultaat, setResultaat] = useState(null);

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

  const payloadPreview = {
    inkomsten_uitgaven: inkomstenPosts.map((post) => ({
      id: post.id,
      type: post.type,
      titel: post.titel,
      ...post.values,
    })),
    vermogen: vermogenPosts.map((post) => ({
      id: post.id,
      type: post.type,
      titel: post.titel,
      ...post.values,
    })),
  };

  const jaarRows = useMemo(() => aggregateYearRows(resultaat?.cashflow), [resultaat]);

  const runBerekening = async () => {
    setIsLoading(true);
    setErrorMessage("");
    try {
      const payload = buildRequestPayload({
        posts,
        persoonNaam,
        geboortedatum,
        jaarVan,
        jaarTot,
      });

      const response = await fetch(`${apiBase}/berekeningen`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
        return;
      }

      setResultaat(data);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Onbekende fout bij berekening");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="page">
      <header className="hero">
        <p className="eyebrow">Nieuwe React UI</p>
        <h1>Pensioenplanner Invoer</h1>
        <p>
          Inkomsten/uitgaven en vermogen zijn gescheiden in duidelijke secties. Elke post is een eigen kaart
          met dynamische invoervelden op basis van het gekozen type.
        </p>

        <div className="toolbar">
          <label className="field">
            <span>API basis</span>
            <input value={apiBase} onChange={(e) => setApiBase(e.target.value)} />
          </label>
          <label className="field">
            <span>Naam</span>
            <input value={persoonNaam} onChange={(e) => setPersoonNaam(e.target.value)} />
          </label>
          <label className="field">
            <span>Geboortedatum</span>
            <input type="date" value={geboortedatum} onChange={(e) => setGeboortedatum(e.target.value)} />
          </label>
          <label className="field">
            <span>Jaar van</span>
            <input type="number" value={jaarVan} onChange={(e) => setJaarVan(e.target.value)} />
          </label>
          <label className="field">
            <span>Jaar tot</span>
            <input type="number" value={jaarTot} onChange={(e) => setJaarTot(e.target.value)} />
          </label>
          <button onClick={runBerekening} disabled={isLoading}>
            {isLoading ? "Berekenen..." : "Bereken via API"}
          </button>
        </div>
        {errorMessage ? <p className="error">{errorMessage}</p> : null}
        <p className="notice">
          Let op: in de huidige backend-berekening sturen vooral sparen/beleggen (startwaarde, inleg,
          rendement) het vermogenssaldo. Eigen woning en hypotheek worden nu vooral als fiscale/
          informatieve posten meegenomen.
        </p>
      </header>

      <section className="section">
        <SectionHeader
          title="Inkomsten / Uitgaven"
          description="Loon, uitkering, pensioen en eenmalige inkomsten/uitgaven als losse tegels."
        />

        <NewPostPicker
          title="Nieuwe post"
          options={inkomstenTypes}
          value={inkomenType}
          onValueChange={setInkomenType}
          onAdd={() => addPost(inkomenType)}
        />

        <div className="tiles">
          {inkomstenPosts.map((post) => (
            <PostCard key={post.id} post={post} onChange={updatePost} onDelete={removePost} />
          ))}
        </div>
      </section>

      <section className="section">
        <SectionHeader
          title="Vermogen"
          description="Sparen, beleggen, eigen woning, overige bezittingen en schulden (hypotheek)."
        />

        <NewPostPicker
          title="Nieuwe post"
          options={vermogenTypes}
          value={vermogenType}
          onValueChange={setVermogenType}
          onAdd={() => addPost(vermogenType)}
        />

        <div className="tiles">
          {vermogenPosts.map((post) => (
            <PostCard key={post.id} post={post} onChange={updatePost} onDelete={removePost} />
          ))}
        </div>
      </section>

      <section className="section">
        <SectionHeader
          title="Resultaten op Jaarbasis"
          description="Uitkomst van de berekening gegroepeerd per jaar."
        />

        {jaarRows.length === 0 ? (
          <p>Voer een berekening uit om jaarresultaten te tonen.</p>
        ) : (
          <>
            <div className="kpis">
              <div className="kpi">
                <span>Periode</span>
                <strong>{`${jaarRows[0].jaar} - ${jaarRows[jaarRows.length - 1].jaar}`}</strong>
              </div>
              <div className="kpi">
                <span>Gemiddeld netto per jaar</span>
                <strong>{euro(jaarRows.reduce((sum, row) => sum + row.netto, 0) / jaarRows.length)}</strong>
              </div>
              <div className="kpi">
                <span>Eindvermogen</span>
                <strong>{euro(jaarRows[jaarRows.length - 1].vermogenEinde)}</strong>
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Jaar</th>
                    <th>Bruto</th>
                    <th>Belasting</th>
                    <th>Netto</th>
                    <th>Netto p/m</th>
                    <th>Vermogen einde jaar</th>
                  </tr>
                </thead>
                <tbody>
                  {jaarRows.map((row) => (
                    <tr key={row.jaar}>
                      <td>{row.jaar}</td>
                      <td>{euro(row.bruto)}</td>
                      <td>{euro(row.belasting)}</td>
                      <td>{euro(row.netto)}</td>
                      <td>{euro(row.nettoPerMaand)}</td>
                      <td>{euro(row.vermogenEinde)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section className="section">
        <SectionHeader
          title="JSON Preview"
          description="Voor API-koppeling: actuele UI-invoer als JSON-structuur."
        />
        <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
      </section>
    </main>
  );
}
