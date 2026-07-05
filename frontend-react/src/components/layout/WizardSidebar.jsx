function statusSymbol(status) {
  if (status === "completed") {
    return "✔";
  }
  if (status === "active") {
    return "●";
  }
  if (status === "error") {
    return "⚠";
  }
  if (status === "stale") {
    return "🔄";
  }
  return "○";
}

export default function WizardSidebar({
  steps,
  activeStep,
  stepStatusMap,
  onStepSelect,
  onCalculate,
  calculationStatus,
  isCalculating,
}) {
  const berekenLabel = calculationStatus === "stale" ? "Herberekenen" : "Berekenen";

  return (
    <aside className="sidebar">
      <p className="sidebar-title">Pensioenplanner</p>
      <p className="sidebar-sub">Voortgang</p>

      <nav className="step-list">
        {steps.map((step, index) => {
          const isCurrent = step.id === activeStep;
          const status = stepStatusMap[step.id] || "pending";
          const className = isCurrent ? "is-current" : status === "completed" ? "is-completed" : "is-upcoming";

          return (
            <button
              key={step.id}
              type="button"
              className={`step-item ${className}`}
              onClick={() => onStepSelect(step.id)}
            >
              <span className="step-num">{String(index + 1).padStart(2, "0")}</span>
              <span className="step-symbol">{statusSymbol(status)}</span>
              <span>{step.label}</span>
            </button>
          );
        })}
      </nav>

      {onCalculate ? (
        <button className="calc-btn" onClick={onCalculate} disabled={isCalculating}>
          {isCalculating ? "Berekenen..." : berekenLabel}
        </button>
      ) : null}
    </aside>
  );
}
