export default function FieldRenderer({ field, value, onChange }) {
  const handleChange = (e) => {
    const newValue = field.type === 'boolean'
      ? e.target.checked
      : e.target.value;
    onChange(newValue);
  };

  const handleArrayChange = (index, newValue) => {
    const arrayValue = Array.isArray(value) ? [...value] : [];
    arrayValue[index] = newValue;
    onChange(arrayValue);
  };

  const handleArrayAdd = () => {
    const arrayValue = Array.isArray(value) ? [...value] : [];
    arrayValue.push('');
    onChange(arrayValue);
  };

  const handleArrayRemove = (index) => {
    const arrayValue = Array.isArray(value) ? [...value] : [];
    arrayValue.splice(index, 1);
    onChange(arrayValue);
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

    case 'array':
      const arrayValue = Array.isArray(value) ? value : (field.default || []);
      const itemType = field.itemType || 'text';

      return (
        <div className="field-array">
          {arrayValue.map((item, index) => (
            <div key={index} className="array-item">
              <input
                type={itemType}
                value={item || ''}
                onChange={(e) => handleArrayChange(index, e.target.value)}
                className="field-input"
              />
              <button
                type="button"
                onClick={() => handleArrayRemove(index)}
                className="btn btn-sm btn-danger array-remove"
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={handleArrayAdd}
            className="btn btn-sm btn-secondary array-add"
          >
            + Add {field.label}
          </button>
        </div>
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
