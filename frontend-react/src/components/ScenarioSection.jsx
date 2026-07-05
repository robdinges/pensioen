export default function ScenarioSection({
  SectionHeader,
  activeScenario,
  activeScenarioId,
  activeScenarioName,
  scenarios,
  newScenarioName,
  setNewScenarioName,
  switchScenario,
  removeActiveScenario,
  renameActiveScenario,
  addScenario,
  duplicateActiveScenario,
  compareScenarioId,
  setCompareScenarioId,
  runScenarioComparison,
  isComparing,
  comparisonError,
  comparisonResult,
  comparisonSummary,
  compareScenarioName,
  signedEuro,
  signedPercentagePoints,
  euro,
  decimalLike,
}) {
  return (
    <section className="section">
      <SectionHeader
        title="Scenario's"
        description="Beheer scenario's binnen het actieve huishouden en kies welk scenario berekend wordt."
      />

      <div className="household-controls">
        <label className="field inline-field">
          <span>Actief scenario</span>
          <select
            value={activeScenario?.id || ""}
            onChange={(e) => switchScenario(e.target.value)}
          >
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.naam || "Onbenoemd scenario"}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="ghost"
          onClick={removeActiveScenario}
          disabled={scenarios.length <= 1}
        >
          Verwijder actief scenario
        </button>
      </div>

      <label className="field inline-field">
        <span>Scenario naam</span>
        <input
          value={activeScenarioName}
          onChange={(e) => renameActiveScenario(e.target.value)}
        />
      </label>

      <div className="household-controls">
        <label className="field inline-field">
          <span>Nieuw scenario</span>
          <input
            value={newScenarioName}
            placeholder="Bijv. Eerder stoppen met werken"
            onChange={(e) => setNewScenarioName(e.target.value)}
          />
        </label>
        <button type="button" onClick={addScenario}>
          Scenario toevoegen
        </button>
        <button type="button" onClick={duplicateActiveScenario}>
          Dupliceer actief scenario
        </button>
      </div>

      <div className="household-controls">
        <label className="field inline-field">
          <span>Vergelijk met scenario</span>
          <select
            value={compareScenarioId}
            onChange={(e) => setCompareScenarioId(e.target.value)}
            disabled={scenarios.length <= 1}
          >
            {scenarios.filter((scenario) => scenario.id !== activeScenarioId).map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.naam || "Onbenoemd scenario"}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={runScenarioComparison} disabled={isComparing || scenarios.length <= 1}>
          {isComparing ? "Vergelijken..." : "Vergelijk scenario's"}
        </button>
      </div>

      {comparisonError ? <p className="error">{comparisonError}</p> : null}

      {comparisonResult?.scenario_resultaten?.length ? (
        <div className="table-wrap import-preview">
          <p className="notice">
            Vergelijking over {comparisonResult.jaar_van} - {comparisonResult.jaar_tot}
            {comparisonResult.beste_scenario_netto?.scenario_naam
              ? ` | Beste mediaan netto: ${comparisonResult.beste_scenario_netto.scenario_naam}`
              : ""}
          </p>
          {comparisonSummary ? (
            <div className="kpis comparison-kpis">
              <div className="kpi comparison-kpi">
                <span>Vergelijkd scenario</span>
                <strong>{compareScenarioName}</strong>
              </div>
              <div className="kpi comparison-kpi">
                <span>Delta netto p/m</span>
                <strong className={comparisonSummary.nettoDelta >= 0 ? "trend-positive" : "trend-negative"}>
                  {signedEuro(comparisonSummary.nettoDelta)}
                </strong>
              </div>
              <div className="kpi comparison-kpi">
                <span>Delta vermogen op 80</span>
                <strong className={comparisonSummary.vermogen80Delta >= 0 ? "trend-positive" : "trend-negative"}>
                  {signedEuro(comparisonSummary.vermogen80Delta)}
                </strong>
              </div>
              <div className="kpi comparison-kpi">
                <span>Delta belastingdruk</span>
                <strong className={comparisonSummary.belastingdrukDelta <= 0 ? "trend-positive" : "trend-negative"}>
                  {signedPercentagePoints(comparisonSummary.belastingdrukDelta)}
                </strong>
              </div>
            </div>
          ) : null}
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Mediaan netto p/m</th>
                <th>Laagste jaar</th>
                <th>Vermogen op 70</th>
                <th>Vermogen op 80</th>
                <th>Belastingdruk</th>
                <th>Tekortjaren</th>
              </tr>
            </thead>
            <tbody>
              {comparisonResult.scenario_resultaten.map((item) => (
                <tr
                  key={item.scenario_naam}
                  className={[
                    "comparison-row",
                    item.scenario_naam === activeScenarioName ? "is-active" : "",
                    item.scenario_naam === comparisonResult.beste_scenario_netto?.scenario_naam ? "is-best" : "",
                  ].filter(Boolean).join(" ")}
                >
                  <td>{item.scenario_naam}</td>
                  <td>{euro(decimalLike(item.netto_per_maand_mediaan))}</td>
                  <td>
                    {item.laagste_inkomensjaar ? `${item.laagste_inkomensjaar}: ${euro(decimalLike(item.netto_laagste_jaar))}` : "-"}
                  </td>
                  <td>{euro(decimalLike(item.vermogen_op_70))}</td>
                  <td>{euro(decimalLike(item.vermogen_op_80))}</td>
                  <td>{`${decimalLike(item.gemiddelde_belastingdruk).toFixed(1)}%`}</td>
                  <td>{item.aantal_tekortjaren ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <p className="notice">
        Het actieve scenario wordt gebruikt als naam in de berekenpayload.
      </p>
    </section>
  );
}