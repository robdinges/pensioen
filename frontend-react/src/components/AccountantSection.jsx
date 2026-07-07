import { useState } from "react";

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

const POST_TYPE_LABEL = {
  loon: "Loon",
  uitkering: "Uitkering",
  pensioen: "Pensioen",
  uitgave: "Uitgave",
  eenmalige_inkomsten: "Eenmalige inkomsten",
  eenmalige_uitgaven: "Eenmalige uitgaven",
  sparen: "Sparen",
  beleggen: "Beleggen",
  eigen_woning: "Eigen woning",
  overige_bezittingen: "Overige bezittingen",
  hypotheek: "Hypotheek",
};

function pct(value, digits = 2) {
  return `${(toNumber(value) * 100).toFixed(digits)}%`;
}

function sumMonths(months, selector) {
  return months.reduce((sum, month) => sum + toNumber(selector(month)), 0);
}

function yearFromIso(value) {
  if (!value || typeof value !== "string") {
    return null;
  }
  const match = value.match(/^(\d{4})-/);
  return match ? Number(match[1]) : null;
}

function isPostActiveInYear(post, year) {
  const values = post?.values || {};
  if (post?.type === "eenmalige_inkomsten" || post?.type === "eenmalige_uitgaven") {
    const datumJaar = yearFromIso(values.datum);
    return datumJaar === year;
  }

  const startJaar = yearFromIso(values.startdatum);
  const eindJaar = yearFromIso(values.einddatum);
  if (startJaar != null && year < startJaar) {
    return false;
  }
  if (eindJaar != null && year > eindJaar) {
    return false;
  }
  return true;
}

function formatPeriode(post) {
  const values = post?.values || {};
  if (post?.type === "eenmalige_inkomsten" || post?.type === "eenmalige_uitgaven") {
    return values.datum || "-";
  }
  const start = values.startdatum || "-";
  const eind = values.einddatum || "-";
  return `${start} t/m ${eind}`;
}

function formatPostBedrag(post, euro) {
  const values = post?.values || {};
  if (values.bedrag !== undefined && values.bedrag !== "") {
    return euro(values.bedrag);
  }
  if (values.beginwaarde !== undefined && values.beginwaarde !== "") {
    return euro(values.beginwaarde);
  }
  return "-";
}

function PostSourceTable({ title, posts, euro }) {
  if (!Array.isArray(posts) || posts.length === 0) {
    return (
      <p className="notice">{title}: geen actieve bronposten in dit jaar.</p>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <caption>{title}</caption>
        <thead>
          <tr>
            <th>Type</th>
            <th>Titel</th>
            <th>Persoon</th>
            <th>Bedrag</th>
            <th>Bedragtype</th>
            <th>Frequentie</th>
            <th>Periode / datum</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post) => (
            <tr key={`bron-${post.id}`}>
              <td>{POST_TYPE_LABEL[post.type] || post.type}</td>
              <td>{post.titel || "-"}</td>
              <td>{post?.values?.persoon || "Huishouden"}</td>
              <td>{formatPostBedrag(post, euro)}</td>
              <td>{post?.values?.bedrag_type || (post.type === "uitgave" ? "netto" : "-")}</td>
              <td>{post?.values?.frequentie || (post.type.startsWith("eenmalige") ? "eenmalig" : "-")}</td>
              <td>{formatPeriode(post)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function YearSummaryTable({ rows, euro }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Post</th>
            <th>P1</th>
            <th>P2</th>
            <th>Huishouden</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <td>{row.label}</td>
              <td>{row.p1 == null ? "-" : euro(row.p1)}</td>
              <td>{row.p2 == null ? "-" : euro(row.p2)}</td>
              <td>{euro(row.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PostSpecificationTable({ title, rows }) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return null;
  }

  return (
    <div className="table-wrap">
      <table>
        <caption>{title}</caption>
        <thead>
          <tr>
            <th>Post</th>
            <th>Definitie</th>
            <th>Specificatie / formule</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${title}-${row.post}`}>
              <td>{row.post}</td>
              <td>{row.definitie}</td>
              <td>{row.formule}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TariefTable({ title, schijven, pctFormatter, euro }) {
  if (!Array.isArray(schijven) || schijven.length === 0) {
    return null;
  }

  return (
    <div className="table-wrap">
      <table>
        <caption>{title}</caption>
        <thead>
          <tr>
            <th>Schijf</th>
            <th>Tot</th>
            <th>Tarief</th>
          </tr>
        </thead>
        <tbody>
          {schijven.map((schijf, index) => (
            <tr key={`${title}-${index}`}>
              <td>{index + 1}</td>
              <td>{schijf.tot == null ? "Geen bovengrens" : euro(schijf.tot)}</td>
              <td>{pctFormatter(schijf.tarief, 3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AccountantYear({ jaarResultaat, euro, posts }) {
  const months = Array.isArray(jaarResultaat?.maanden) ? jaarResultaat.maanden : [];
  if (months.length === 0) {
    return null;
  }
  const controlejaar = Number(jaarResultaat.jaar);
  const actieveBronposten = Array.isArray(posts)
    ? posts.filter((post) => isPostActiveInYear(post, controlejaar))
    : [];

  const tarieven = months[0]?.gebruikte_tarieven || {};
  const persoon1 = tarieven.persoon1 || {};
  const persoon2 = tarieven.persoon2 || null;
  const box3 = tarieven.box3 || {};

  const brutoP1 = sumMonths(months, (month) => month.arbeid_p1_bruto + month.aow_p1_bruto + month.pensioen_p1_bruto);
  const brutoP2 = sumMonths(months, (month) => month.arbeid_p2_bruto + month.aow_p2_bruto + month.pensioen_p2_bruto);
  const arbeidP1 = sumMonths(months, (month) => month.arbeid_p1_bruto);
  const arbeidP2 = sumMonths(months, (month) => month.arbeid_p2_bruto);
  const aowP1 = sumMonths(months, (month) => month.aow_p1_bruto);
  const aowP2 = sumMonths(months, (month) => month.aow_p2_bruto);
  const pensioenP1 = sumMonths(months, (month) => month.pensioen_p1_bruto);
  const pensioenP2 = sumMonths(months, (month) => month.pensioen_p2_bruto);
  const overig = sumMonths(months, (month) => month.overig_bruto);
  const rente = sumMonths(months, (month) => month.rente_bruto);
  const nettoComponenten = sumMonths(months, (month) => month.inkomen_componenten_netto);
  const belastingP1 = sumMonths(months, (month) => month.belasting_p1);
  const belastingP2 = sumMonths(months, (month) => month.belasting_p2);
  const heffingskortingP1 = sumMonths(months, (month) => month.heffingskorting_p1);
  const heffingskortingP2 = sumMonths(months, (month) => month.heffingskorting_p2);
  const box3Heffing = sumMonths(months, (month) => month.box3_heffing);
  const inhoudingen = sumMonths(months, (month) => month.inhoudingen);
  const uitgaven = sumMonths(months, (month) => month.huishoudelijke_uitgaven);
  const eenmaligOntvangst = sumMonths(months, (month) => month.eenmalig_ontvangst);
  const eenmaligUitgave = sumMonths(months, (month) => month.eenmalig_uitgave);
  const netto = sumMonths(months, (month) => month.netto ?? 0);
  const eindVermogen = toNumber(months[months.length - 1]?.vermogen_einde_maand);
  const effectiefTarief = brutoP1 + brutoP2 + overig + rente > 0
    ? Math.max(0, ((belastingP1 + belastingP2 + box3Heffing) - (heffingskortingP1 + heffingskortingP2)) / (brutoP1 + brutoP2 + overig + rente) * 100)
    : 0;

  const summaryRows = [
    { label: "Arbeidsinkomen bruto", p1: arbeidP1, p2: arbeidP2, total: arbeidP1 + arbeidP2 },
    { label: "AOW bruto", p1: aowP1, p2: aowP2, total: aowP1 + aowP2 },
    { label: "Pensioen bruto", p1: pensioenP1, p2: pensioenP2, total: pensioenP1 + pensioenP2 },
    { label: "Overig bruto", p1: null, p2: null, total: overig },
    { label: "Rente / rendement", p1: null, p2: null, total: rente },
    { label: "Netto componenten", p1: null, p2: null, total: nettoComponenten },
    { label: "Belasting box 1", p1: belastingP1, p2: belastingP2, total: belastingP1 + belastingP2 },
    { label: "Heffingskortingen", p1: heffingskortingP1, p2: heffingskortingP2, total: heffingskortingP1 + heffingskortingP2 },
    { label: "Box 3 heffing", p1: null, p2: null, total: box3Heffing },
    { label: "Inhoudingen", p1: null, p2: null, total: inhoudingen },
    { label: "Huishoudelijke uitgaven", p1: null, p2: null, total: uitgaven },
    { label: "Eenmalige ontvangst", p1: null, p2: null, total: eenmaligOntvangst },
    { label: "Eenmalige uitgave", p1: null, p2: null, total: eenmaligUitgave },
    { label: "Netto jaarresultaat", p1: null, p2: null, total: netto },
  ];

  const grondslagRows = [
    { label: "Bruto jaarinkomen", p1: persoon1.grondslagen?.bruto_jaarinkomen ?? brutoP1, p2: persoon2?.grondslagen?.bruto_jaarinkomen ?? brutoP2, total: (persoon1.grondslagen?.bruto_jaarinkomen ?? brutoP1) + (persoon2?.grondslagen?.bruto_jaarinkomen ?? brutoP2) },
    { label: "Arbeidsinkomen grondslag", p1: persoon1.grondslagen?.arbeidsinkomen ?? arbeidP1, p2: persoon2?.grondslagen?.arbeidsinkomen ?? arbeidP2, total: (persoon1.grondslagen?.arbeidsinkomen ?? arbeidP1) + (persoon2?.grondslagen?.arbeidsinkomen ?? arbeidP2) },
    { label: "Premiegrondslag", p1: persoon1.grondslagen?.premiegrondslag ?? 0, p2: persoon2?.grondslagen?.premiegrondslag ?? 0, total: (persoon1.grondslagen?.premiegrondslag ?? 0) + (persoon2?.grondslagen?.premiegrondslag ?? 0) },
    { label: "Box 3 startvermogen", p1: null, p2: null, total: box3.grondslag_start_vermogen ?? 0 },
    { label: "Box 3 vrijstelling", p1: null, p2: null, total: box3.vrijstelling ?? 0 },
    { label: "Box 3 belastbaar vermogen", p1: null, p2: null, total: box3.belastbaar_vermogen ?? 0 },
    { label: "Box 3 fictief rendement", p1: null, p2: null, total: box3.fictief_rendement ?? 0 },
  ];

  const kortingRows = [
    { label: "Algemene heffingskorting", p1: persoon1.ahk ?? 0, p2: persoon2?.ahk ?? 0, total: (persoon1.ahk ?? 0) + (persoon2?.ahk ?? 0) },
    { label: "Arbeidskorting", p1: persoon1.arbeidskorting ?? 0, p2: persoon2?.arbeidskorting ?? 0, total: (persoon1.arbeidskorting ?? 0) + (persoon2?.arbeidskorting ?? 0) },
    { label: "Ouderenkorting", p1: persoon1.ouderenkorting ?? 0, p2: persoon2?.ouderenkorting ?? 0, total: (persoon1.ouderenkorting ?? 0) + (persoon2?.ouderenkorting ?? 0) },
    { label: "Alleenstaande ouderenkorting", p1: persoon1.alleenstaandeouderenkorting ?? 0, p2: persoon2?.alleenstaandeouderenkorting ?? 0, total: (persoon1.alleenstaandeouderenkorting ?? 0) + (persoon2?.alleenstaandeouderenkorting ?? 0) },
  ];

  const jaaroverzichtSpecificaties = [
    {
      post: "Arbeidsinkomen bruto",
      definitie: "Bruto arbeidsinkomen uit componenten per persoon.",
      formule: "Som van maandvelden arbeid_p1_bruto en arbeid_p2_bruto over 12 maanden.",
    },
    {
      post: "AOW bruto",
      definitie: "Automatisch berekende AOW-bedragen per persoon.",
      formule: "Som van maandvelden aow_p1_bruto en aow_p2_bruto.",
    },
    {
      post: "Pensioen bruto",
      definitie: "Bruto pensioeninkomen uit pensioencomponenten.",
      formule: "Som van maandvelden pensioen_p1_bruto en pensioen_p2_bruto.",
    },
    {
      post: "Overig bruto",
      definitie: "Overige bruto inkomenscomponenten in het huishouden.",
      formule: "Som van maandveld overig_bruto.",
    },
    {
      post: "Rente / rendement",
      definitie: "Maandelijkse vermogensopbrengst uit vermogen_engine.",
      formule: "Som van maandveld rente_bruto.",
    },
    {
      post: "Netto componenten",
      definitie: "Netto ingevoerde componenten die niet in bruto-belastinggrondslag vallen.",
      formule: "Som van maandveld inkomen_componenten_netto.",
    },
    {
      post: "Belasting box 1",
      definitie: "Toegerekende maandbelasting persoon 1 en 2 (jaarbelasting / 12).",
      formule: "Som van maandvelden belasting_p1 + belasting_p2.",
    },
    {
      post: "Heffingskortingen",
      definitie: "Toegerekende maandheffingskortingen persoon 1 en 2 (jaarkorting / 12).",
      formule: "Som van maandvelden heffingskorting_p1 + heffingskorting_p2.",
    },
    {
      post: "Box 3 heffing",
      definitie: "Toegerekende maandbox-3-heffing op startvermogen van het jaar.",
      formule: "Som van maandveld box3_heffing.",
    },
    {
      post: "Inhoudingen",
      definitie: "Periodieke inhoudingen uit scenario-componenten.",
      formule: "Som van maandveld inhoudingen.",
    },
    {
      post: "Huishoudelijke uitgaven",
      definitie: "Periodieke uitgaven op huishoudniveau.",
      formule: "Som van maandveld huishoudelijke_uitgaven.",
    },
    {
      post: "Eenmalige ontvangst / uitgave",
      definitie: "Incidentele posten op exacte datum in het jaar.",
      formule: "Som van maandvelden eenmalig_ontvangst en eenmalig_uitgave.",
    },
    {
      post: "Netto jaarresultaat",
      definitie: "Geaggregeerde netto cashflow van het kalenderjaar.",
      formule: "Som van maandveld netto over alle maanden.",
    },
  ];

  const grondslagSpecificaties = [
    {
      post: "Bruto jaarinkomen",
      definitie: "Belastinggrondslag bruto per persoon uit gebruikte tarievenpayload.",
      formule: "persoonX.grondslagen.bruto_jaarinkomen (fallback op bruto-som uit maandvelden).",
    },
    {
      post: "Arbeidsinkomen grondslag",
      definitie: "Arbeidsinkomen dat meetelt voor arbeidskorting en delen van box-1-berekening.",
      formule: "persoonX.grondslagen.arbeidsinkomen (fallback op arbeid-som uit maandvelden).",
    },
    {
      post: "Premiegrondslag",
      definitie: "Grondslag voor AOW/Anw/Wlz-premies tot premiegrens.",
      formule: "persoonX.grondslagen.premiegrondslag.",
    },
    {
      post: "Box 3 grondslagregels",
      definitie: "Startvermogen, vrijstelling, belastbaar vermogen en fictief rendement.",
      formule: "box3.grondslag_start_vermogen, box3.vrijstelling, box3.belastbaar_vermogen, box3.fictief_rendement.",
    },
  ];

  const kortingSpecificaties = [
    {
      post: "Algemene heffingskorting",
      definitie: "AHK volgens jaarconfig en AOW-breuk.",
      formule: "persoonX.ahk.",
    },
    {
      post: "Arbeidskorting",
      definitie: "Arbeidskorting op basis van arbeidsinkomen en afbouwdrempel.",
      formule: "persoonX.arbeidskorting.",
    },
    {
      post: "Ouderenkorting",
      definitie: "Ouderenkorting op basis van AOW-status en inkomen.",
      formule: "persoonX.ouderenkorting.",
    },
    {
      post: "Alleenstaande ouderenkorting",
      definitie: "Aanvullende korting indien van toepassing op alleenstaande AOW-situatie.",
      formule: "persoonX.alleenstaandeouderenkorting.",
    },
  ];

  return (
    <div>
      <SectionHeaderBlock
        jaar={jaarResultaat.jaar}
        tarievenJaar={jaarResultaat.tarieven_jaar}
        tarievenAanname={jaarResultaat.tarieven_aanname}
        netto={netto}
        eindVermogen={eindVermogen}
        effectiefTarief={effectiefTarief}
        euro={euro}
      />

      <h3>Jaaroverzicht</h3>
      <YearSummaryTable rows={summaryRows} euro={euro} />
      <PostSpecificationTable
        title="Specificatie posten - Jaaroverzicht"
        rows={jaaroverzichtSpecificaties}
      />

      <h3>Grondslagen en tussentotalen</h3>
      <YearSummaryTable rows={grondslagRows} euro={euro} />
      <PostSpecificationTable
        title="Specificatie posten - Grondslagen"
        rows={grondslagSpecificaties}
      />

      <h3>Heffingskortingen</h3>
      <YearSummaryTable rows={kortingRows} euro={euro} />
      <PostSpecificationTable
        title="Specificatie posten - Heffingskortingen"
        rows={kortingSpecificaties}
      />

      <h3>Specificatie bronposten (actief in dit jaar)</h3>
      <PostSourceTable
        title={`Bronposten controlejaar ${jaarResultaat.jaar}`}
        posts={actieveBronposten}
        euro={euro}
      />

      <h3>Belastingtarieven en premies</h3>
      <div className="kpis">
        <div className="kpi"><span>AOW-breuk P1</span><strong>{pct(persoon1.aow_breuk ?? 0, 1)}</strong></div>
        <div className="kpi"><span>AOW-breuk P2</span><strong>{pct(persoon2?.aow_breuk ?? 0, 1)}</strong></div>
        <div className="kpi"><span>Inkomstenbelasting P1</span><strong>{euro(persoon1.inkomstenbelasting ?? 0)}</strong></div>
        <div className="kpi"><span>Inkomstenbelasting P2</span><strong>{euro(persoon2?.inkomstenbelasting ?? 0)}</strong></div>
      </div>

      <TariefTable title="Schijven niet-AOW" schijven={persoon1.schijven?.box1_niet_aow} pctFormatter={pct} euro={euro} />
      <TariefTable title="Schijven AOW" schijven={persoon1.schijven?.box1_aow} pctFormatter={pct} euro={euro} />

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Premie / tarief</th>
              <th>Waarde</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Premiegrens</td><td>{euro(persoon1.premies_config?.premiegrens ?? 0)}</td></tr>
            <tr><td>AOW-premie niet-AOW</td><td>{pct(persoon1.premies_config?.aow_tarief_niet_aow ?? 0, 3)}</td></tr>
            <tr><td>AOW-premie AOW</td><td>{pct(persoon1.premies_config?.aow_tarief_aow ?? 0, 3)}</td></tr>
            <tr><td>Anw-premie</td><td>{pct(persoon1.premies_config?.anw_tarief ?? 0, 3)}</td></tr>
            <tr><td>Wlz-premie</td><td>{pct(persoon1.premies_config?.wlz_tarief ?? 0, 3)}</td></tr>
            <tr><td>Box 3 forfait spaargeld</td><td>{pct(box3.forfaitair_spaargeld ?? 0, 3)}</td></tr>
            <tr><td>Box 3 forfait overig</td><td>{pct(box3.forfaitair_overig ?? 0, 3)}</td></tr>
            <tr><td>Box 3 gewogen forfait</td><td>{pct(box3.gewogen_forfait ?? 0, 3)}</td></tr>
            <tr><td>Box 3 tarief</td><td>{pct(box3.tarief ?? 0, 3)}</td></tr>
            <tr><td>Box 3 spaargeldfractie</td><td>{pct(box3.spaargeld_fractie ?? 0, 3)}</td></tr>
          </tbody>
        </table>
      </div>

      {jaarResultaat.tarieven_aanname ? <p className="notice">Tariefaanname: {jaarResultaat.tarieven_aanname}</p> : null}
      {box3.disclaimer ? <p className="notice">Box 3: {box3.disclaimer}</p> : null}
      {Array.isArray(months[0]?.aannames) && months[0].aannames.length > 0 ? (
        <div className="notice">
          <strong>Aannames</strong>
          <ul>
            {months[0].aannames.map((aanname) => (
              <li key={`${jaarResultaat.jaar}-${aanname}`}>{aanname}</li>
            ))}
          </ul>
        </div>
      ) : null}

    </div>
  );
}

function SectionHeaderBlock({ jaar, tarievenJaar, tarievenAanname, netto, eindVermogen, effectiefTarief, euro }) {
  const gebruiktTariefjaar = Number(tarievenJaar || jaar);
  const controlejaar = Number(jaar);
  const isFallbackTarief = Number.isFinite(gebruiktTariefjaar) && Number.isFinite(controlejaar) && gebruiktTariefjaar !== controlejaar;

  return (
    <>
      <div className="section-header">
        <h3>{`Controlejaar ${jaar}`}</h3>
        <p>
          {`Belastingjaar gebruikt: ${tarievenJaar || jaar}`}
          {isFallbackTarief ? " (fallback op laatstbekend jaar)" : ""}
          {tarievenAanname ? ` · ${tarievenAanname}` : ""}
        </p>
      </div>
      <div className="kpis">
        <div className="kpi"><span>Netto jaar</span><strong>{euro(netto)}</strong></div>
        <div className="kpi"><span>Eindvermogen</span><strong>{euro(eindVermogen)}</strong></div>
        <div className="kpi"><span>Effectieve belastingdruk</span><strong>{effectiefTarief.toFixed(2)}%</strong></div>
      </div>
    </>
  );
}

export default function AccountantSection({ SectionHeader, resultaat, euro, posts }) {
  const jaren = Array.isArray(resultaat?.cashflow?.jaren) ? resultaat.cashflow.jaren : [];
  const [expandedYears, setExpandedYears] = useState({});

  const toggleYear = (jaar) => {
    setExpandedYears((prev) => ({
      ...prev,
      [jaar]: !prev[jaar],
    }));
  };

  return (
    <section className="section">
      <SectionHeader
        title="Accountant"
        description="Controle-overzicht met herleidbare jaartotalen, grondslagen, tarieven en tussentotalen per belastingjaar."
      />
      {jaren.length === 0 ? (
        <p>Voer eerst een berekening uit om de accountantscontrole te tonen.</p>
      ) : (
        jaren.map((jaarResultaat) => {
          const jaar = jaarResultaat.jaar;
          const isExpanded = Boolean(expandedYears[jaar]);

          return (
            <article className="section" key={jaar}>
              <div className="household-controls">
                <p className="notice">{`Controlejaar ${jaar}`}</p>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => toggleYear(jaar)}
                >
                  {isExpanded ? "Inklappen" : "Uitklappen"}
                </button>
              </div>
              {isExpanded ? (
                <AccountantYear jaarResultaat={jaarResultaat} euro={euro} posts={posts} />
              ) : (
                <p className="notice">Jaar is ingeklapt. Klik op Uitklappen voor detail.</p>
              )}
            </article>
          );
        })
      )}
    </section>
  );
}