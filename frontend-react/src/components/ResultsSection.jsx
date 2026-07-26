import { useState } from "react";

function TrendChart({ title, rows, series, euro }) {
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
      <svg className="trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={padding.left} x2={width - padding.right} y1={y(tick)} y2={y(tick)} className="chart-gridline" />
            <text x={padding.left - 12} y={y(tick) + 4} textAnchor="end" className="chart-axis-label">
              {new Intl.NumberFormat("nl-NL", { notation: "compact", maximumFractionDigits: 1 }).format(tick)}
            </text>
          </g>
        ))}
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
                    <circle cx={point.x} cy={point.y} r="4" fill={item.color} />
                    <circle
                      cx={point.x}
                      cy={point.y}
                      r="14"
                      fill="transparent"
                      className="chart-hit-area"
                      tabIndex="0"
                      aria-label={`${row.jaar}, ${item.label}: ${euro(row[item.key])}`}
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
    </article>
  );
}

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
          <div className="charts-stack">
            <TrendChart
              title="Inkomen over de berekeningsperiode"
              rows={jaarRows}
              euro={euro}
              series={[
                { key: "bruto", label: "Bruto inkomen", color: "#557c3e" },
                { key: "netto", label: "Netto inkomen", color: "#165d48" },
                { key: "cashflow", label: "Vrije cashflow", color: "#b54f3f" },
              ]}
            />
            <TrendChart
              title="Vermogensontwikkeling"
              rows={jaarRows}
              euro={euro}
              series={[
                { key: "vermogenEinde", label: "Vermogen einde jaar", color: "#b56b2f" },
              ]}
            />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Jaar</th><th>Bruto</th><th>Belasting</th><th>Netto inkomen</th><th>Vrije cashflow</th><th>Vermogen einde jaar</th></tr>
              </thead>
              <tbody>
                {jaarRows.map((row) => (
                  <tr key={row.jaar}>
                    <td>{row.jaar}</td><td>{euro(row.bruto)}</td><td>{euro(row.belasting)}</td><td>{euro(row.netto)}</td><td>{euro(row.cashflow)}</td><td>{euro(row.vermogenEinde)}</td>
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
