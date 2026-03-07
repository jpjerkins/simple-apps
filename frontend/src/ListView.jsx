import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ListView({ schema }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const loadItems = () => {
    setLoading(true);
    fetch(`/api/${schema.id}/items`)
      .then(res => res.json())
      .then(data => {
        setItems(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load items:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadItems();
  }, [schema.id]);

  const handleDelete = (itemId) => {
    if (!confirm('Are you sure you want to delete this item?')) {
      return;
    }

    fetch(`/api/${schema.id}/items/${itemId}`, {
      method: 'DELETE'
    })
      .then(() => {
        loadItems();
      })
      .catch(err => {
        console.error('Failed to delete item:', err);
        alert('Failed to delete item');
      });
  };

  const displayFields = schema.fields.filter(f => f.displayInList);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="list-view">
      <div className="list-header">
        <h1>
          <span className="app-icon">{schema.icon}</span>
          {schema.name}
        </h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate(`/${schema.id}/new`)}
        >
          + Add Item
        </button>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <p>No items yet. Click "Add Item" to create one.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                {displayFields.map(field => (
                  <th key={field.id}>{field.label}</th>
                ))}
                <th className="actions-column">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id}>
                  {displayFields.map(field => (
                    <td key={field.id}>
                      {formatValue(item[field.id], field)}
                    </td>
                  ))}
                  <td className="actions-column">
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => navigate(`/${schema.id}/edit/${item.id}`)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(item.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function formatValue(value, field) {
  if (value === null || value === undefined || value === '') {
    return '-';
  }

  if (field.type === 'boolean') {
    return value ? '✓' : '✗';
  }

  if (field.type === 'date' && value) {
    return new Date(value).toLocaleDateString();
  }

  return String(value);
}
