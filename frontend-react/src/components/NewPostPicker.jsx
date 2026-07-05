export default function NewPostPicker({ title, options, value, onValueChange, onAdd, labelMap }) {
  return (
    <div className="add-row">
      <h4>{title}</h4>
      <div>
        <select value={value} onChange={(e) => onValueChange(e.target.value)}>
          {options.map((option) => (
            <option key={option} value={option}>
              {labelMap[option]}
            </option>
          ))}
        </select>
        <button onClick={onAdd}>+ Post toevoegen</button>
      </div>
    </div>
  );
}