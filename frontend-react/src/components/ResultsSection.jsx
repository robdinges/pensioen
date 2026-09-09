import { selectChartPeriod } from "../planner/chartPeriod.js";
import YearIncomeDetails from "./YearIncomeDetails";
import ScenarioComparison from "./ScenarioComparison";
import { useState } from "react";
import { computeStopmomentSummary } from "../planner/plannerCore.js";

function TrendChart({ title, rows, series, euro, gekozenJaar, onJaarSelect }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const width = 900;
  const height = 250;
  const padding = { top: 24, right: 24, bottom: 38, left: 72 };
  const values = rows.flatMap((row) => series.map((item) => Number(row[item.key]) || 0));
  const minValue = Math.min(0, ...values);
  const maxValue = Math.max(1, ...values);
  const range = maxValue - minValue || 1;
  const x = (index) => padding.left + (index * (width - padding.left - padding.right)) / Math.max(1, rows.length - 1);
  const y = (value) => padding.top + ((maxValue - value) * (height - padding.top - padding.bottom)) / range;
  const ticks = [maxValue, minValue + range / 2, minValue];
  const labelIndexes = [...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])];

  return (
    <article className="chart-card">
      <div className="chart-heading">
        <h3>{title}</h3>
        <div className="chart-legend">
          {series.map((item) => (
            <span key={item.key}><i style={{ background: item.color }} />{item.label}</span>
          ))}
        </div>
      </div>
      <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} role="group" aria-label={title}>
        {rows.map((row, index) => row.jaar === gekozenJaar ? <line key={`selection-${row.jaar}`} x1={x(index)} x2={x(index)} y1={padding.top} y2={height - padding.bottom} className="chart-selected-year" /> : null)}
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} className="chart-gridline" />
            <text x={padding.left - 12} y={y(tick) + 4} textAnchor="end" className="chart-axis-label">
              {new Intl.NumberFormat("nl-NL", { notation: "compact", maximumFractionDigits: 1 }).format(tick)}
            </text>
          </g>
        ))}
        {minValue < 0 && maxValue > 0 ? <line x1={padding.left} x2={width - padding.right} y1={y(0)} y2={y(0)} stroke="#73857c" strokeDasharray="5 5" /> : null}
        <text x={padding.left} y="14" className="chart-axis-label">Bedragen in euro</text>
        {series.map((item) => {
          const points = rows.map((row, index) => `${x(index)},${y(Number(row[item.key]) || 0)}`).join(" ");
          return (
            <g key={item.key}>
              <polyline points={points} fill="none" stroke={item.color} strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
              {rows.map((row, index) => {
                const point = {
                  x: x(index),
                  y: y(Number(row[item.key]) || 0),
                  jaar: row.jaar,
                  label: item.label,
                  value: row[item.key],
                  color: item.color,
                };
                return (
                  <g key={`${item.key}-${row.jaar}`}>
                    <circle cx={point.x} cy={point.y} r={row.jaar === gekozenJaar ? "6" : "4"} fill={item.color} />
                    <circle
                      cx={point.x}
                      cy={point.y}
                      r="14"
                      fill="transparent"
                      className="chart-hit-area"
                      tabIndex="0"
                      role="button"
                      aria-pressed={row.jaar === gekozenJaar}
                      onClick={() => onJaarSelect(row.jaar)}
                      onKeyDown={event => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          onJaarSelect(row.jaar);
                        }
                      }}
                      aria-label={`Bekijk ${row.jaar}, ${item.label}: ${euro(row[item.key])}`}
                      onMouseEnter={() => setHoveredPoint(point)}
                      onMouseLeave={() => setHoveredPoint(null)}
                      onFocus={() => setHoveredPoint(point)}
                      onBlur={() => setHoveredPoint(null)}
                    />
                  </g>
                );
              })}
            </g>
          );
        })}
        {labelIndexes.map((index) => (
          <text key={rows[index].jaar} x={x(index)} y={height - 12} textAnchor="middle" className="chart-axis-label">
            {rows[index].jaar}
          </text>
        ))}
        {hoveredPoint ? (
          <g className="chart-tooltip" pointerEvents="none">
            <rect
              x={Math.min(width - 238, Math.max(padding.left, hoveredPoint.x - 110))}
              y={Math.max(4, hoveredPoint.y - 62)}
              width="220"
              height="48"
              rx="8"
            />
            <text
              x={Math.min(width - 228, Math.max(padding.left + 10, hoveredPoint.x - 100))}
              y={Math.max(22, hoveredPoint.y - 43)}
            >
              <tspan fontWeight="700">{hoveredPoint.jaar} · {hoveredPoint.label}</tspan>
              <tspan
                x={Math.min(width - 228, Math.max(padding.left + 10, hoveredPoint.x - 100))}
                dy="18"
                fill={hoveredPoint.color}
              >
                {euro(hoveredPoint.value)}
              </tspan>
            </text>
          </g>
        ) : null}
      </svg>
      <p className="chart-selection-help">Klik op een punt of gebruik Tab en Enter/spatie. Gekozen jaar: {gekozenJaar}.</p>
    </article>
  );
}

export default function ResultsSection({
  SectionHeader,
  jaarRows,
  jaren = [],
  euro,
  aannames = [],
  calculationStatus,
  onStepSelect,
  comparisonResult,
  activeScenarioName,
  geboortedatum = "",
  partnerGeboortedatum = "",
  scenarios = [], activeScenarioId, compareScenarioId = "", thirdScenarioId = "",
  setCompareScenarioId, setThirdScenarioId, runScenarioComparison,
  isComparing = false, comparisonError = "",

}) {
  const stopmoment = computeStopmomentSummary(jaarRows, geboortedatum);
  const [gekozenJaar, setGekozenJaar] = useState("");
  const jaar = jaarRows.find(row => String(row.jaar) === gekozenJaar) || jaarRows[0];
  const [grafiekVan, setGrafiekVan] = useState("");
  const [grafiekTot, setGrafiekTot] = useState("");
  const grafiekRows = selectChartPeriod(jaarRows, grafiekVan, grafiekTot);
  const selecteerJaar = waarde => {
    setGekozenJaar(String(waarde));
    if (!grafiekRows.some(row => String(row.jaar) === String(waarde))) {
      setGrafiekVan(""); setGrafiekTot("");
    }
  };
  const wijzigPeriode = (van, tot) => {
    setGrafiekVan(String(van)); setGrafiekTot(String(tot));
    const rows = selectChartPeriod(jaarRows, van, tot);
    if (!rows.some(row => row.jaar === jaar?.jaar)) setGekozenJaar(String(rows[0].jaar));
  };
  const laatsteJaar = jaarRows.at(-1);
  const alternatieven = scenarios.filter(item => item.id !== activeScenarioId);


  return (
    <section className="section results-dashboard">
      <SectionHeader title="Je pensioenplan in beeld" description="Inzicht in je inkomen, je buffer en de keuzes voor later." />
      {jaarRows.length === 0 ? (
        <div className="empty-state">
          <h3>Hoe ziet jouw financiële toekomst eruit?</h3>
          <p>Vul je inkomen, uitgaven en vermogen in. Kies daarna bovenaan ‘Bekijk mijn pensioenplan’.</p>
          <button type="button" onClick={() => onStepSelect("componenten")}>Inkomen & vermogen invullen</button>
        </div>
      ) : (
        <>
          {calculationStatus !== "fresh" ? <p className="feedback-banner warning" role="status">Deze uitkomsten horen bij een eerdere berekening. Bereken opnieuw om je huidige invoer te bekijken.</p> : null}
          <div className="dashboard-hero">
            <div><span className="dashboard-eyebrow">Jouw financiële vooruitblik</span>
              <h3>{activeScenarioName || "Je pensioenplan"}</h3>
              <p>{jaarRows[0].jaar}–{laatsteJaar.jaar} · Bedragen voor het huishouden</p>
            </div>
            <div className="dashboard-status"><span>Plancontrole</span><strong>{calculationStatus === "fresh" ? stopmoment.stopMomentLabel : "Bereken opnieuw"}</strong></div>
          </div>
          <div className="dashboard-heading">
            <div><h3>Wat betekent dit voor je geld?</h3><p>De kaarten tonen jaarbedragen voor {jaar.jaar}. De grafiekperiode kies je hieronder; scenario’s tonen de hele berekeningsperiode.</p></div>
            <label className="field"><span>Bekijk jaar</span><select value={jaar.jaar} onChange={event => selecteerJaar(event.target.value)}>
              {jaarRows.map(row => <option key={row.jaar} value={row.jaar}>{row.jaar}</option>)}
            </select></label>
          </div>
          <div className="dashboard-kpis">
            <article className="dashboard-kpi"><span>Netto inkomen</span><strong>{euro(jaar.netto)}</strong><small>Na belasting · in {jaar.jaar}</small></article>
            <article className={`dashboard-kpi ${jaar.cashflow < 0 ? "is-negative" : "is-positive"}`}><span>{jaar.cashflow < 0 ? "Aan te vullen uit vermogen" : "Over na geldstromen"}</span><strong>{euro(Math.abs(jaar.cashflow))}</strong><small>Vrije cashflow · {jaar.cashflow < 0 ? "tekort" : "overschot"} in {jaar.jaar}</small></article>
            <article className={`dashboard-kpi ${jaar.vermogenEinde < 0 ? "is-negative" : ""}`}><span>Vermogen einde jaar</span><strong>{euro(jaar.vermogenEinde)}</strong><small>Verwachte stand eind {jaar.jaar}</small></article>
            <article className="dashboard-kpi"><span>Belasting</span><strong>{euro(jaar.belasting)}</strong><small>Berekend over {jaar.jaar}</small></article>
          </div>
          {calculationStatus === "fresh" ? <div className="notice" role="status">
            <strong>Plancontrole:</strong> {stopmoment.summaryText}
            {stopmoment.firstShortfallYear !== null ? ` Eerste tekortjaar: ${stopmoment.firstShortfallYear}.` : ""}
            {stopmoment.wealthAt80 === null ? " Vermogen op 80: niet beschikbaar binnen deze berekeningsperiode." : ` Vermogen eind jaar waarin persoon 1 80 wordt: ${euro(stopmoment.wealthAt80)}.`}
          </div> : null}
          <p className="notice">Netto inkomen is je inkomen na belasting. Vrije cashflow laat zien wat er na de overige geldstromen overblijft; een negatief bedrag betekent dat je inteert op je vermogen.</p>
          {aannames.length > 0 ? (
            <details className="assumptions-panel">
              <summary>Uitgangspunten en gebruikte tarieven ({aannames.length})</summary>
              <ul>{aannames.map((aanname, index) => <li key={index}>{aanname}</li>)}</ul>
            </details>
          ) : null}
          <div className="dashboard-comparison-controls" aria-label="Grafiekperiode">
            <label className="field"><span>Grafieken vanaf</span><select value={grafiekRows[0].jaar} onChange={event => wijzigPeriode(event.target.value, grafiekRows.at(-1).jaar)}>
              {jaarRows.filter(row => row.jaar <= grafiekRows.at(-1).jaar).map(row => <option key={row.jaar} value={row.jaar}>{row.jaar}</option>)}
            </select></label>
            <label className="field"><span>Grafieken tot en met</span><select value={grafiekRows.at(-1).jaar} onChange={event => wijzigPeriode(grafiekRows[0].jaar, event.target.value)}>
              {jaarRows.filter(row => row.jaar >= grafiekRows[0].jaar).map(row => <option key={row.jaar} value={row.jaar}>{row.jaar}</option>)}
            </select></label>
            <button type="button" className="ghost" onClick={() => { setGrafiekVan(""); setGrafiekTot(""); }}>Hele periode</button>
          </div>
          <p className="chart-selection-help">Beide grafieken tonen {grafiekRows[0].jaar}–{grafiekRows.at(-1).jaar}. De assen schalen mee. Kies je bovenaan een jaar buiten deze periode, dan tonen de grafieken weer de hele periode.</p>
          <div className="charts-stack">
            <TrendChart
              title="Je inkomen en bestedingsruimte · per jaar"
              rows={grafiekRows}
              gekozenJaar={jaar.jaar}
              onJaarSelect={selecteerJaar}
              euro={euro}
              series={[
                { key: "bruto", label: "Bruto inkomen", color: "#557c3e" },
                { key: "netto", label: "Netto inkomen", color: "#165d48" },
                { key: "cashflow", label: "Vrije cashflow", color: "#b54f3f" },
              ]}
            />
            <TrendChart
              title="Hoe ontwikkelt je vermogen zich? · einde jaar"
              rows={grafiekRows}
              gekozenJaar={jaar.jaar}
              onJaarSelect={selecteerJaar}
              euro={euro}
              series={[
                { key: "vermogenEinde", label: "Vermogen einde jaar", color: "#b56b2f" },
              ]}
            />
          </div>
          <section className="dashboard-selected-detail" aria-label="Details gekozen jaar">
            <h3 aria-live="polite">Jaardetails · {jaar.jaar}</h3>
            <div className="table-wrap"><table>
              <caption>Bedragen voor het gekozen jaar {jaar.jaar}</caption>
              <thead><tr><th scope="col">Jaar</th><th scope="col">Bruto</th><th scope="col">Belasting</th><th scope="col">Netto inkomen</th><th scope="col">Vrije cashflow</th><th scope="col">Vermogen einde jaar</th></tr></thead>
              <tbody><tr><th scope="row">{jaar.jaar}</th><td>{euro(jaar.bruto)}</td><td>{euro(jaar.belasting)}</td><td>{euro(jaar.netto)}</td><td>{euro(jaar.cashflow)}</td><td>{euro(jaar.vermogenEinde)}</td></tr></tbody>
            </table></div>
            <YearIncomeDetails jaar={jaar.jaar} jaren={jaren} euro={euro} />
          </section>
          <div className="dashboard-scenarios">
            <div className="dashboard-heading"><div><span className="dashboard-eyebrow">Keuzes naast elkaar</span><h3>Vergelijk je scenario’s</h3><p>Ontdek wat een ander plan betekent voor je bestedingsruimte en buffer.</p></div>
              <button type="button" className="ghost" onClick={() => onStepSelect("scenario")}>Scenario’s beheren</button>
            </div>
            {alternatieven.length > 0 ? <div className="dashboard-comparison-controls">
              <label className="field"><span>Vergelijk met</span><select value={compareScenarioId} disabled={isComparing} onChange={event => { setCompareScenarioId(event.target.value); if (event.target.value === thirdScenarioId) setThirdScenarioId(""); }}>
                <option value="" disabled>Kies een scenario</option>
                {alternatieven.map(item => <option key={item.id} value={item.id}>{item.naam}</option>)}
              </select></label>
              <label className="field"><span>Derde scenario (optioneel)</span><select value={thirdScenarioId} disabled={isComparing} onChange={event => setThirdScenarioId(event.target.value)}>
                <option value="">Geen derde scenario</option>
                {alternatieven.filter(item => item.id !== compareScenarioId).map(item => <option key={item.id} value={item.id}>{item.naam}</option>)}
              </select></label>
              <button type="button" disabled={isComparing || !compareScenarioId} onClick={runScenarioComparison}>{isComparing ? "Scenario’s berekenen…" : "Vergelijk scenario’s"}</button>
            </div> : !comparisonResult ? <p className="notice">Maak een kopie van je plan via ‘Scenario’s beheren’ en pas bijvoorbeeld je stopdatum aan. Daarna zie je hier de verschillen.</p> : null}
            {comparisonError ? <p className="feedback-banner warning" role="alert">{comparisonError}</p> : null}
            {comparisonResult ? <ScenarioComparison comparisonResult={comparisonResult} activeScenarioName={activeScenarioName} euro={euro} geboortedatum={geboortedatum} partnerGeboortedatum={partnerGeboortedatum} /> : alternatieven.length > 0 ? <p className="notice">Kies je alternatieven en vergelijk opnieuw om actuele verschillen te bekijken.</p> : null}
          </div>
          <details className="dashboard-year-detail"><summary>Alle jaarbedragen bekijken · {jaarRows[0].jaar}–{laatsteJaar.jaar}</summary>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Jaar</th><th>Bruto</th><th>Belasting</th><th>Netto inkomen</th><th>Vrije cashflow</th><th>Vermogen einde jaar</th></tr>
              </thead>
              <tbody>
                {jaarRows.map((row) => (
                  <tr key={row.jaar} className={row.jaar === jaar.jaar ? "is-selected-year" : undefined}>
                    <td>{row.jaar}</td><td>{euro(row.bruto)}</td><td>{euro(row.belasting)}</td><td>{euro(row.netto)}</td><td>{euro(row.cashflow)}</td><td>{euro(row.vermogenEinde)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          </details>
        </>
      )}
    </section>
  );
}
