function ImportPreviewTable({ title, rows }) {
  if (!rows || rows.length === 0) {
    return null;
  }

  return (
    <div className="table-wrap import-preview">
      <p className="notice">{title}</p>
      <table>
        <thead>
          <tr>
            <th>Uitvoerder</th>
            <th>Regeling</th>
            <th>Type</th>
            <th>Ingangsdatum</th>
            <th>Bruto/jaar</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={`${row.uitvoerder}-${row.regeling}-${idx}`}>
              <td>{row.uitvoerder || "-"}</td>
              <td>{row.regeling || "-"}</td>
              <td>{row.type || "-"}</td>
              <td>{row.ingangsdatum || "-"}</td>
              <td>{row.bruto_per_jaar || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ImportStatsPanel({ persoonCode, stats }) {
  if (!stats) {
    return null;
  }

  const items = [
    { label: "Bronregels", value: stats.bronregels },
    { label: "Geimporteerd", value: stats.geimporteerd },
    { label: "Overgeslagen type", value: stats.overgeslagenType },
    { label: "Overgeslagen bedrag", value: stats.overgeslagenBedrag },
    { label: "Duplicaten", value: stats.overgeslagenDuplicaat },
  ];

  return (
    <div className="import-stats-panel">
      <p className="notice import-subtitle">Samenvatting {persoonCode}</p>
      <div className="import-stats-grid">
        {items.map((item) => (
          <div key={`${persoonCode}-${item.label}`} className="import-stat-card">
            <span>{item.label}</span>
            <strong>{item.value ?? 0}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function ImportWarningsPanel({ persoonCode, warnings }) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <div className="import-warning-panel">
      <p className="notice warning import-subtitle">Controlepunten {persoonCode}</p>
      <ul className="validation-list import-warning-list">
        {warnings.map((melding) => (
          <li key={`${persoonCode}-${melding}`}>{melding}</li>
        ))}
      </ul>
    </div>
  );
}

function ImportPersoonBlok({
  persoonCode,
  label,
  disabled,
  bestandsNaam,
  previewRows,
  stats,
  warnings,
  infoMessage,
  errorMessage,
  onImportFile,
}) {
  return (
    <>
      <div className="household-controls">
        <label className="field inline-field">
          <span>{label}</span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.json,.pdf"
            disabled={disabled}
            onChange={(e) => {
              const file = e.target.files?.[0] || null;
              if (file) {
                onImportFile(file, persoonCode);
              }
            }}
          />
        </label>
        <span className="notice">
          {disabled
            ? "Import bezig..."
            : bestandsNaam
              ? `Laatst: ${bestandsNaam}`
              : "Nog geen bestand"}
        </span>
      </div>

      <ImportPreviewTable title={`Preview import ${label.toLowerCase()}`} rows={previewRows} />
      <ImportStatsPanel persoonCode={persoonCode} stats={stats} />
      <ImportWarningsPanel persoonCode={persoonCode} warnings={warnings} />
      {infoMessage ? <p className="notice">{infoMessage}</p> : null}
      {errorMessage ? <p className="error">{errorMessage}</p> : null}
    </>
  );
}

export default function MpoImportSection({
  heeftPartner,
  isImportingP1,
  isImportingP2,
  importBestandP1Naam,
  importBestandP2Naam,
  importPreviewP1,
  importPreviewP2,
  importStatsP1,
  importStatsP2,
  importWarningsP1,
  importWarningsP2,
  importInfoMessages,
  importErrorMessages,
  onImportFile,
  SectionHeader,
}) {
  return (
    <section className="section">
      <SectionHeader
        title="Pensioengegevens Import"
        description="Importeer MPO-bestanden en zet ouderdomspensioenen direct om naar pensioen-componenten."
      />

      <p className="notice">
        Ondersteund in deze stap: CSV, Excel (.xlsx/.xls), JSON en PDF.
      </p>

      <ImportPersoonBlok
        persoonCode="P1"
        label="MPO-bestand persoon 1"
        disabled={isImportingP1}
        bestandsNaam={importBestandP1Naam}
        previewRows={importPreviewP1}
        stats={importStatsP1}
        warnings={importWarningsP1}
        infoMessage={importInfoMessages.P1}
        errorMessage={importErrorMessages.P1}
        onImportFile={onImportFile}
      />

      {heeftPartner ? (
        <ImportPersoonBlok
          persoonCode="P2"
          label="MPO-bestand persoon 2"
          disabled={isImportingP2}
          bestandsNaam={importBestandP2Naam}
          previewRows={importPreviewP2}
          stats={importStatsP2}
          warnings={importWarningsP2}
          infoMessage={importInfoMessages.P2}
          errorMessage={importErrorMessages.P2}
          onImportFile={onImportFile}
        />
      ) : (
        <p className="notice">Partner staat uit. Schakel P2 in op de stap Personen om voor P2 te importeren.</p>
      )}
    </section>
  );
}