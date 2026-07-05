export default function ResultsSection({ SectionHeader, jaarRows, euro }) {
  return (
    <section className="section">
      <SectionHeader title="Resultaten op Jaarbasis" description="Uitkomst van de berekening gegroepeerd per jaar." />
      {jaarRows.length === 0 ? (
        <p>Voer een berekening uit om jaarresultaten te tonen.</p>
      ) : (
        <>
          <div className="kpis">
            <div className="kpi"><span>Periode</span><strong>{`${jaarRows[0].jaar} - ${jaarRows[jaarRows.length - 1].jaar}`}</strong></div>
            <div className="kpi"><span>Gemiddeld netto per jaar</span><strong>{euro(jaarRows.reduce((sum, row) => sum + row.netto, 0) / jaarRows.length)}</strong></div>
            <div className="kpi"><span>Eindvermogen</span><strong>{euro(jaarRows[jaarRows.length - 1].vermogenEinde)}</strong></div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Jaar</th><th>Bruto</th><th>Belasting</th><th>Netto</th><th>Netto p/m</th><th>Vermogen einde jaar</th></tr>
              </thead>
              <tbody>
                {jaarRows.map((row) => (
                  <tr key={row.jaar}>
                    <td>{row.jaar}</td><td>{euro(row.bruto)}</td><td>{euro(row.belasting)}</td><td>{euro(row.netto)}</td><td>{euro(row.nettoPerMaand)}</td><td>{euro(row.vermogenEinde)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}