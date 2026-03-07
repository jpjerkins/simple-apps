import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import FieldRenderer from './components/FieldRenderer';

export default function FormView({ schema, isEdit }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (isEdit && id) {
      fetch(`/api/${schema.id}/items/${id}`)
        .then(res => res.json())
        .then(data => {
          setFormData(data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to load item:', err);
          alert('Failed to load item');
          navigate(`/${schema.id}`);
        });
    } else {
      const defaults = {};
      schema.fields.forEach(field => {
        if (field.default !== undefined) {
          defaults[field.id] = field.default;
        }
      });
      setFormData(defaults);
    }
  }, [schema.id, id, isEdit]);

  const handleFieldChange = (fieldId, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const url = isEdit
      ? `/api/${schema.id}/items/${id}`
      : `/api/${schema.id}/items`;

    const method = isEdit ? 'PUT' : 'POST';

    const submitData = { ...formData };
    delete submitData.id;
    delete submitData.created_at;
    delete submitData.updated_at;

    fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(submitData)
    })
      .then(res => res.json())
      .then(() => {
        navigate(`/${schema.id}`);
      })
      .catch(err => {
        console.error('Failed to save item:', err);
        alert('Failed to save item');
      });
  };

  const handleCancel = () => {
    navigate(`/${schema.id}`);
  };

  const shouldShowField = (field) => {
    if (!field.showIf) {
      return true;
    }

    for (const [fieldName, expectedValue] of Object.entries(field.showIf)) {
      const actualValue = formData[fieldName];

      if (Array.isArray(expectedValue)) {
        if (!expectedValue.includes(actualValue)) {
          return false;
        }
      } else {
        if (actualValue !== expectedValue) {
          return false;
        }
      }
    }

    return true;
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="form-view">
      <div className="form-header">
        <h1>
          <span className="app-icon">{schema.icon}</span>
          {isEdit ? 'Edit' : 'New'} {schema.name}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="data-form">
        {schema.fields.filter(shouldShowField).map(field => (
          <div key={field.id} className="form-field">
            <label htmlFor={field.id} className="field-label">
              {field.label}
              {field.required && <span className="required">*</span>}
            </label>
            <FieldRenderer
              field={field}
              value={formData[field.id]}
              onChange={(value) => handleFieldChange(field.id, value)}
            />
          </div>
        ))}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            {isEdit ? 'Save' : 'Create'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
