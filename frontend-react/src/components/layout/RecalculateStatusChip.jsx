const STATUS_LABELS = {
  idle: "Nog niet berekend",
  stale: "Herberekening nodig",
  fresh: "Alles actueel",
  calculating: "Berekening loopt",
};

export default function RecalculateStatusChip({ status }) {
  const safeStatus = STATUS_LABELS[status] ? status : "idle";
  return <span className={`status-chip ${safeStatus}`}>{STATUS_LABELS[safeStatus]}</span>;
}
