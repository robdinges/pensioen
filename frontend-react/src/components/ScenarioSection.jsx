import ScenarioComparison from "./ScenarioComparison";

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
  thirdScenarioId,
  setThirdScenarioId,
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
        <label className="field inline-field">
          <span>Derde scenario (optioneel)</span>
          <select value={thirdScenarioId} onChange={e => setThirdScenarioId(e.target.value)}>
            <option value="">Geen derde scenario</option>
            {scenarios.filter(item => item.id !== activeScenarioId && item.id !== compareScenarioId).map(item => (
              <option key={item.id} value={item.id}>{item.naam}</option>
            ))}
          </select>
        </label>
        <button type="button" onClick={runScenarioComparison} disabled={isComparing || scenarios.length <= 1}>
          {isComparing ? "Vergelijken..." : "Vergelijk scenario's"}
        </button>
      </div>

      {comparisonError ? <p className="error">{comparisonError}</p> : null}

      {comparisonResult?.scenario_resultaten?.length ? (
        <ScenarioComparison comparisonResult={comparisonResult} activeScenarioName={activeScenarioName} euro={euro} />
      ) : null}
    </section>
  );
}
