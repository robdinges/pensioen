export default function ReportSection({
  SectionHeader,
  downloadRapport,
  isReportLoading,
  canCalculate,
  reportErrorMessage,
}) {
  return (
    <section className="section">
      <SectionHeader
        title="Rapport"
        description="Download een Excel-rapport via het API endpoint /rapportages/excel."
      />
      <p className="notice">
        Het rapport wordt gegenereerd op basis van de huidige invoer in het actieve huishouden en scenario.
      </p>
      <div className="household-controls">
        <button type="button" onClick={downloadRapport} disabled={isReportLoading || !canCalculate}>
          {isReportLoading ? "Rapport genereren..." : "Download Excel-rapport"}
        </button>
      </div>
      {reportErrorMessage ? <p className="error">{reportErrorMessage}</p> : null}
    </section>
  );
}