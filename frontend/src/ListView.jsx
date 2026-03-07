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
  const groupBy = schema.views?.list?.groupBy;

  const groupItems = (items, groupByField) => {
    if (!groupByField) {
      return { 'All Items': items };
    }

    const groups = {};
    items.forEach(item => {
      const groupValue = item[groupByField] || 'Uncategorized';
      if (!groups[groupValue]) {
        groups[groupValue] = [];
      }
      groups[groupValue].push(item);
    });
    return groups;
  };

  const renderItemRow = (item) => (
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
  );

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  const groupedItems = groupItems(items, groupBy);

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
        <>
          {Object.entries(groupedItems).map(([groupName, groupItems]) => (
            <div key={groupName} className="group-section">
              {groupBy && <h2 className="group-header">{formatGroupName(groupName)}</h2>}
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
                    {groupItems.map(renderItemRow)}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
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

function formatGroupName(groupName) {
  return groupName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
