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
  const hasBalance = config.section === "vermogen" && post.type !== "hypotheek";
  const balances = Array.isArray(post.values.saldostanden) ? post.values.saldostanden : [];
  const baseDate = post.values.peildatum ?? post.values.startdatum ?? "";
  const latest = [{ peildatum: baseDate, bedrag: post.values.beginwaarde }, ...balances]
    .filter(s => s.bedrag !== "" && s.bedrag != null).sort((a, b) => (a.peildatum || "").localeCompare(b.peildatum || "")).at(-1);
  const period = hasBalance
    ? (latest?.peildatum ? `Stand op ${latest.peildatum}` : "Stand bij start berekeningsperiode")
    : post.values.datum || `${post.values.startdatum ? `Vanaf ${post.values.startdatum}` : "Geen begindatum"} · ${post.values.einddatum ? `T/m ${post.values.einddatum}` : "Geen einddatum"}`;
  const updateBalance = (index, field, value) => onChange(post.id, "saldostanden",
    balances.map((stand, i) => i === index ? { ...stand, [field]: value } : stand));
  const summaryItems = [
    post.values.persoon,
    amountField ? formatAmount(hasBalance ? latest?.bedrag : post.values[amountField]) : null,
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
            const value = field === "peildatum" ? baseDate : post.values[field] ?? "";

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
                {meta.type === "date" && !value ? <small>{
                  field === "startdatum" ? "Geen begindatum: geldt vanaf het begin van de berekeningsperiode."
                    : field === "einddatum" ? "Geen einddatum: loopt door tot het einde van de berekening."
                    : field === "peildatum" ? "Geen peildatum ingevuld: dit saldo geldt bij de start van de berekeningsperiode."
                    : "Geen datum ingevuld."
                }</small> : null}
              </label>
            );
          })}
        </div>
        {hasBalance ? <section aria-label="Saldostanden">
          <p>Dit is een stand op een peildatum, geen looptijd. De waarde groeit door met het opgegeven rendement. Een nieuwere stand vervangt de berekende waarde op die datum.</p>
          {post.values.einddatum ? <p>De eerder ingevulde einddatum {post.values.einddatum} wordt voor deze bezitting niet meer als einddatum gebruikt.</p> : null}
          {balances.map((stand, index) => <div className="grid compact-grid" key={index}>
            <label className="field"><span>Nieuwe peildatum</span>
              <input type="date" value={stand.peildatum || ""} onChange={e => updateBalance(index, "peildatum", e.target.value)} />
              {!stand.peildatum ? <small>Vul de datum van deze stand in.</small> : null}
            </label>
            <label className="field"><span>Saldo / waarde op die datum</span>
              <input type="number" min="0" step="0.01" value={stand.bedrag ?? ""} onChange={e => updateBalance(index, "bedrag", e.target.value)} />
            </label>
            <button type="button" className="ghost" onClick={() => onChange(post.id, "saldostanden", balances.filter((_, i) => i !== index))}>Verwijder stand</button>
          </div>)}
          <button type="button" onClick={() => onChange(post.id, "saldostanden", [...balances, { peildatum: "", bedrag: "" }])}>Nieuwe saldostand toevoegen</button>
        </section> : null}
      </div>
    </details>
  );
}
