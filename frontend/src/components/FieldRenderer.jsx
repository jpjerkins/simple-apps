export default function FieldRenderer({ field, value, onChange }) {
  const handleChange = (e) => {
    const newValue = field.type === 'boolean'
      ? e.target.checked
      : e.target.value;
    onChange(newValue);
  };

  const fieldValue = value ?? field.default ?? '';

  switch (field.type) {
    case 'text':
      return (
        <input
          type="text"
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          required={field.required}
          className="field-input"
        />
      );

    case 'textarea':
      return (
        <textarea
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          required={field.required}
          className="field-textarea"
          rows="4"
        />
      );

    case 'date':
      return (
        <input
          type="date"
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          required={field.required}
          className="field-input"
        />
      );

    case 'number':
      return (
        <input
          type="number"
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          required={field.required}
          className="field-input"
        />
      );

    case 'select':
      return (
        <select
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          required={field.required}
          className="field-select"
        >
          <option value="">Select...</option>
          {field.options.map(option => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );

    case 'boolean':
      return (
        <input
          type="checkbox"
          id={field.id}
          checked={fieldValue === true}
          onChange={handleChange}
          className="field-checkbox"
        />
      );

    default:
      return (
        <input
          type="text"
          id={field.id}
          value={fieldValue}
          onChange={handleChange}
          className="field-input"
        />
      );
  }
}
