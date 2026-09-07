function amount(value, euro) {
  return value == null ? "Niet beschikbaar" : euro(Number(value));
}

function monthLabel(value) {
  return value ? new Intl.DateTimeFormat("nl-NL", {month:"long",year:"numeric"})
    .format(new Date(`${value}-01T12:00:00`)) : "";
}

function leeftijdOpDatum(geboortedatum, datum) {
  if (!geboortedatum || !datum) return null;
  const geboorte = new Date(`${geboortedatum}T12:00:00`);
  const werkdag = new Date(`${datum}T12:00:00`);
  let jaren = werkdag.getFullYear() - geboorte.getFullYear();
  const verjaardagNogNietGeweest = werkdag.getMonth() < geboorte.getMonth()
    || (werkdag.getMonth() === geboorte.getMonth() && werkdag.getDate() < geboorte.getDate());
  if (verjaardagNogNietGeweest) jaren -= 1;
  let maanden = (werkdag.getFullYear() - (geboorte.getFullYear() + jaren)) * 12
    + werkdag.getMonth() - geboorte.getMonth();
  if (werkdag.getDate() < geboorte.getDate()) maanden -= 1;
  return `${jaren}j ${maanden} m`;
}

export default function ScenarioComparison({ comparisonResult, activeScenarioName, euro, geboortedatum, partnerGeboortedatum }) {
  const context = comparisonResult?.klantvergelijking;
  const results = comparisonResult?.scenario_resultaten || [];
  if (!context || results.some(item => !item.klantbeeld?.jaarregels)
      || context.actief_scenario !== activeScenarioName) {
    return <p className="notice">Vergelijk opnieuw om de begrijpelijke scenariokaarten te zien.</p>;
  }
  const averageLabel = context.na_stoppen ? "Gemiddeld over per maand na stoppen" : "Gemiddeld over per maand";
  const hasMonths = results.some(item => item.klantbeeld.aantal_maanden_gemiddelde > 0);
  return (
    <div className="scenario-comparison">
      <h3>Wat betekent elk scenario voor je geld?</h3>
      <p className="notice">
        {hasMonths ? <>Het gemiddelde gebruikt voor elk scenario dezelfde periode: {context.gemiddelde_van} t/m {context.gemiddelde_tot}.
          {context.na_stoppen ? " Vanaf de eerste volledige maand nadat iedereen in alle scenario’s is gestopt." : " Er is geen volledig stopmoment vastgelegd voor het werkinkomen; daarom gebruiken we de hele berekeningsperiode."}</>
          : "Er zijn binnen de berekeningsperiode geen volledige maanden nadat iedereen in alle scenario’s is gestopt. Het gemiddelde na stoppen is daarom niet beschikbaar."}
        {" Bedragen zijn na belasting en uitgaven, inclusief berekend rendement en eenmalige geldstromen. Een minbedrag betekent dat je vermogen aanspreekt."}
      </p>
      <p>Buffer, jaartekort en jaaropbouw gaan over de volledige periode {context.horizon_van}–{context.horizon_tot}. Verschillen zijn ten opzichte van <strong>{activeScenarioName}</strong>.</p>
      <div className="scenario-cards">
        {results.map(item => {
          const kpi = item.klantbeeld;
          const delta = kpi.verschil_gemiddeld_over_per_maand == null ? null : Number(kpi.verschil_gemiddeld_over_per_maand);
          const wealthDelta = kpi.verschil_vermogen_op_80 == null ? null : Number(kpi.verschil_vermogen_op_80);
          const active = item.scenario_naam === activeScenarioName;
          return (
            <article className={`scenario-card ${active ? "is-active" : ""}`} key={item.scenario_naam}>
              <h3>{item.scenario_naam}</h3>
              {active ? <small>Je actieve plan · uitgangspunt voor de vergelijking</small> : <small>Alternatief voor {activeScenarioName}</small>}
                {Object.entries(kpi.laatste_werkdagen || {}).map(([persoon, datum]) => {
                  const leeftijd = kpi.leeftijden_op_laatste_werkdag?.[persoon]
                    ?? leeftijdOpDatum(persoon === "P2" ? partnerGeboortedatum : geboortedatum, datum);
                  return (
                    <small className="scenario-work-end" key={persoon}>
                      Laatste werkdag {persoon}: {datum || "niet vastgelegd"}
                      {leeftijd != null ? ` (${leeftijd})` : ""}
                    </small>
                  );
                })}
              <dl className="scenario-metrics">
                <div className="scenario-primary"><dt>{averageLabel}</dt><dd>{amount(kpi.gemiddeld_over_per_maand, euro)}</dd><small>Een negatief bedrag is een gemiddeld tekort.</small></div>
                <div><dt>Grootste jaarlijkse tekort</dt><dd>{amount(kpi.grootste_jaartekort, euro)}</dd><small>{kpi.grootste_jaartekort_jaar ? `Aan te vullen uit vermogen in ${kpi.grootste_jaartekort_jaar}` : "Geen jaar met negatieve cashflow"}</small></div>
                <div><dt>Laagste verwachte vermogensbuffer</dt><dd className={Number(kpi.laagste_buffer) < 0 ? "trend-negative" : ""}>{amount(kpi.laagste_buffer, euro)}</dd><small>{monthLabel(kpi.laagste_buffer_maand)} · laagste berekende maandultimo</small></div>
                <div><dt>Verwacht vermogen op je 80e</dt><dd>{amount(kpi.vermogen_op_80, euro)}</dd><small>{kpi.vermogen_op_80 == null ? "Buiten de berekeningsperiode" : "Einde van het jaar waarin persoon 1 80 wordt"}</small></div>
                <div><dt>Jaren waarin je vermogen aanspreekt</dt><dd>{kpi.jaren_interen}</dd><small>Jaren met negatieve cashflow; je buffer kan dit opvangen.</small></div>
              </dl>
              <p className="scenario-explanation">
                {active ? "Dit is het uitgangspunt voor de verschillen." : delta === null ? "Het gemiddelde na stoppen is nog niet te vergelijken."
                  : delta === 0 ? `Gemiddeld evenveel over per maand als bij ${activeScenarioName}.`
                  : `Gemiddeld ${euro(Math.abs(delta))} ${delta < 0 ? "minder" : "meer"} over per maand dan bij ${activeScenarioName}.`}
                {!active && wealthDelta !== null ? ` Op je 80e ${euro(Math.abs(wealthDelta))} ${wealthDelta < 0 ? "minder" : wealthDelta > 0 ? "meer" : "verschil in"} vermogen.` : ""}
                {` Je spreekt in ${kpi.jaren_interen} jaar vermogen aan.`}
                {kpi.jaren_negatief_vermogen > 0 ? ` Let op: in ${kpi.jaren_negatief_vermogen} jaar wordt een negatief saldo berekend; daar is aanvullende dekking nodig.`
                  : " Er is geen negatief maandeindsaldo berekend."}
              </p>
              <details className="scenario-year-detail">
                <summary>Bekijk jaaropbouw · {kpi.jaren_interen} jaren met interen</summary>
                <div className="table-wrap"><table>
                  <thead><tr><th>Jaar</th><th>Over na uitgaven</th><th>Uit vermogen nodig</th><th>Vermogen einde jaar</th><th>Negatief saldo in dit jaar?</th></tr></thead>
                  <tbody>{kpi.jaarregels.map(row => <tr key={row.jaar} className={Number(row.interen) > 0 ? "scenario-interen" : ""}>
                    <td>{row.jaar}</td><td>{amount(row.over_na_uitgaven,euro)}</td><td>{amount(row.interen,euro)}</td><td>{amount(row.vermogen_eind,euro)}</td><td>{row.negatief_vermogen ? "Ja" : "Nee"}</td>
                  </tr>)}</tbody>
                </table></div>
              </details>
            </article>
          );
        })}
      </div>
      <details className="scenario-technical"><summary>Rekendetails</summary>
        <p>Belastingdruk en de oude mediaan zijn technische vergelijkingscijfers over de hele horizon. De mediaan is de middelste waarde en verschilt van het gemiddelde op de kaarten.</p>
        <div className="table-wrap"><table><thead><tr><th>Scenario</th><th>Mediaan vrije cashflow per maand</th><th>Gemiddelde belastingdruk</th></tr></thead>
          <tbody>{results.map(item => <tr key={item.scenario_naam}><td>{item.scenario_naam}</td><td>{amount(item.netto_per_maand_mediaan,euro)}</td><td>{Number(item.gemiddelde_belastingdruk).toLocaleString('nl-NL',{maximumFractionDigits:1})}%</td></tr>)}</tbody>
        </table></div>
      </details>
    </div>
  );
}
