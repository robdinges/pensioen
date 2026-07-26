function formatAmount(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) {
    return value;
  }
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function PostCard({ post, onChange, onDelete, config, fieldMeta }) {
  const amountField = config.fields.find((field) => ["bedrag", "beginwaarde", "maandlast"].includes(field));
  const period = post.values.datum
    || [post.values.startdatum, post.values.einddatum].filter(Boolean).join(" – ");
  const summaryItems = [
    post.values.persoon,
    amountField ? formatAmount(post.values[amountField]) : null,
    post.values.frequentie,
    period,
  ].filter(Boolean);

  return (
    <details className="card component-card">
      <summary className="component-summary">
        <div>
          <span className="component-type">{config.label}</span>
          <h3>{post.titel || config.label}</h3>
          <p>{summaryItems.join(" · ") || config.hint}</p>
        </div>
        <span className="chevron" aria-hidden="true">⌄</span>
      </summary>

      <div className="component-editor">
        <div className="card-top compact-card-top">
          <label className="field component-title-field">
            <span>Titel</span>
            <input
              type="text"
              value={post.titel}
              onChange={(e) => onChange(post.id, "titel", e.target.value, true)}
            />
          </label>
          <button type="button" className="ghost compact-delete" onClick={() => onDelete(post.id)}>
            Verwijder
          </button>
        </div>

        <div className="grid compact-grid">
          {config.fields.map((field) => {
            const meta = fieldMeta[field];
            const value = post.values[field] ?? "";

            if (meta.type === "select") {
              return (
                <label key={field} className="field">
                  <span>{meta.label}</span>
                  <select value={value} onChange={(e) => onChange(post.id, field, e.target.value)}>
                    {meta.options.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
              );
            }

            return (
              <label key={field} className="field">
                <span>{meta.label}</span>
                <input
                  type={meta.type}
                  value={value}
                  step={meta.step}
                  onChange={(e) => onChange(post.id, field, e.target.value)}
                />
              </label>
            );
          })}
        </div>
      </div>
    </details>
  );
}
