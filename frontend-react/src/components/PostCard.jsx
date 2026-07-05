export default function PostCard({ post, onChange, onDelete, config, fieldMeta }) {
  return (
    <article className="card">
      <div className="card-top">
        <div>
          <h3>{config.label}</h3>
          <p>{config.hint}</p>
        </div>
        <button className="ghost" onClick={() => onDelete(post.id)}>
          Verwijder
        </button>
      </div>

      <label className="field">
        <span>Titel</span>
        <input
          type="text"
          value={post.titel}
          onChange={(e) => onChange(post.id, "titel", e.target.value, true)}
        />
      </label>

      <div className="grid">
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
    </article>
  );
}