function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function pct(value, digits = 2) {
  return `${(toNumber(value) * 100).toFixed(digits)}%`;
}

function monthLabel(month) {
  return new Intl.DateTimeFormat("nl-NL", { month: "short" }).format(new Date(2026, month - 1, 1));
}

function sumMonths(months, selector) {
  return months.reduce((sum, month) => sum + toNumber(selector(month)), 0);
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

function AccountantYear({ jaarResultaat, euro }) {
  const months = Array.isArray(jaarResultaat?.maanden) ? jaarResultaat.maanden : [];
  if (months.length === 0) {
    return null;
  }

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

  return (
    <article className="section" key={jaarResultaat.jaar}>
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

      <h3>Grondslagen en tussentotalen</h3>
      <YearSummaryTable rows={grondslagRows} euro={euro} />

      <h3>Heffingskortingen</h3>
      <YearSummaryTable rows={kortingRows} euro={euro} />

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

      <h3>Maandcontrole</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Maand</th>
              <th>Arbeid P1</th>
              <th>Arbeid P2</th>
              <th>AOW P1</th>
              <th>AOW P2</th>
              <th>Pensioen P1</th>
              <th>Pensioen P2</th>
              <th>Overig</th>
              <th>Rente</th>
              <th>Belasting P1</th>
              <th>Belasting P2</th>
              <th>HK P1</th>
              <th>HK P2</th>
              <th>Box 3</th>
              <th>Inhoudingen</th>
              <th>Uitgaven</th>
              <th>Eenmalig +</th>
              <th>Eenmalig -</th>
              <th>Netto</th>
              <th>Vermogen eind</th>
            </tr>
          </thead>
          <tbody>
            {months.map((month) => (
              <tr key={`${jaarResultaat.jaar}-${month.maand}`}>
                <td>{monthLabel(month.maand)}</td>
                <td>{euro(month.arbeid_p1_bruto)}</td>
                <td>{euro(month.arbeid_p2_bruto)}</td>
                <td>{euro(month.aow_p1_bruto)}</td>
                <td>{euro(month.aow_p2_bruto)}</td>
                <td>{euro(month.pensioen_p1_bruto)}</td>
                <td>{euro(month.pensioen_p2_bruto)}</td>
                <td>{euro(month.overig_bruto)}</td>
                <td>{euro(month.rente_bruto)}</td>
                <td>{euro(month.belasting_p1)}</td>
                <td>{euro(month.belasting_p2)}</td>
                <td>{euro(month.heffingskorting_p1)}</td>
                <td>{euro(month.heffingskorting_p2)}</td>
                <td>{euro(month.box3_heffing)}</td>
                <td>{euro(month.inhoudingen)}</td>
                <td>{euro(month.huishoudelijke_uitgaven)}</td>
                <td>{euro(month.eenmalig_ontvangst)}</td>
                <td>{euro(month.eenmalig_uitgave)}</td>
                <td>{euro(month.netto ?? 0)}</td>
                <td>{euro(month.vermogen_einde_maand)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
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

export default function AccountantSection({ SectionHeader, resultaat, euro }) {
  const jaren = Array.isArray(resultaat?.cashflow?.jaren) ? resultaat.cashflow.jaren : [];

  return (
    <section className="section">
      <SectionHeader
        title="Accountant"
        description="Controle-overzicht met herleidbare jaarbedragen, grondslagen, tarieven en maandregels per belastingjaar."
      />
      {jaren.length === 0 ? (
        <p>Voer eerst een berekening uit om de accountantscontrole te tonen.</p>
      ) : (
        jaren.map((jaarResultaat) => (
          <AccountantYear key={jaarResultaat.jaar} jaarResultaat={jaarResultaat} euro={euro} />
        ))
      )}
    </section>
  );
}