// Filter uitsluitend bestaande jaarregels; bedragen blijven engine-output.
export function selectChartPeriod(rows, from = "", to = "") {
  if (!rows.length) return [];
  const start = rows.find(row => String(row.jaar) === String(from))?.jaar ?? rows[0].jaar;
  const end = rows.find(row => String(row.jaar) === String(to))?.jaar ?? rows.at(-1).jaar;
  if (start > end) return rows;
  return rows.filter(row => row.jaar >= start && row.jaar <= end);
}
