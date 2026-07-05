import RecalculateStatusChip from "./RecalculateStatusChip";

export default function ContextTopBar({
  currentHousehold,
  activeScenario,
  calculationStatus,
  lastCalculatedAt,
  autosaveStatus,
  onCalculate,
  isCalculating,
  canCalculate,
}) {
  const berekenLabel = calculationStatus === "stale" ? "Herberekenen" : "Berekenen";

  return (
    <header className="context-topbar">
      <div className="context-meta">
        <div>
          <span>Huishouden</span>
          <strong>{currentHousehold}</strong>
        </div>
        <div>
          <span>Actief scenario</span>
          <strong>{activeScenario}</strong>
        </div>
      </div>

      <div className="context-actions">
        <RecalculateStatusChip status={calculationStatus} />
        <button onClick={onCalculate} disabled={isCalculating || !canCalculate}>
          {isCalculating ? "Berekenen..." : berekenLabel}
        </button>
      </div>

      <div className="context-footnote">
        <span>{autosaveStatus === "saving" ? "Opslaan..." : "Automatisch opgeslagen"}</span>
        {!canCalculate ? <span>Controleer personen en periode voordat je berekent.</span> : null}
        {lastCalculatedAt ? <span>Laatst berekend: {new Date(lastCalculatedAt).toLocaleString("nl-NL")}</span> : null}
      </div>
    </header>
  );
}
