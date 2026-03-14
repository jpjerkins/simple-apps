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
  const computedFields = schema.views?.list?.showComputed ? (schema.views?.list?.computed || {}) : {};

  const computeFieldValue = (item, expression) => {
    try {
      // Create a safe context with only the item data
      const context = { ...item };

      // Handle common expressions
      if (expression === 'usages.length') {
        return Array.isArray(item.usages) ? item.usages.length : 0;
      }

      if (expression === 'usages[usages.length - 1]') {
        return Array.isArray(item.usages) && item.usages.length > 0
          ? item.usages[item.usages.length - 1]
          : null;
      }

      if (expression.includes('Date.now()') && expression.includes('startDate')) {
        // Days active calculation
        const startDate = new Date(item.startDate);

        // For retired razors, use last usage date; for active, use today
        let endDate;
        if (item.status === 'retired' && Array.isArray(item.usages) && item.usages.length > 0) {
          const lastUsage = item.usages[item.usages.length - 1];
          endDate = new Date(lastUsage);
        } else {
          endDate = new Date();
        }

        const days = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24));
        return days;
      }

      return null;
    } catch (error) {
      console.error('Error computing field:', error);
      return null;
    }
  };

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
      {Object.entries(computedFields).map(([fieldId, fieldConfig]) => (
        <td key={`computed-${fieldId}`}>
          {formatComputedValue(
            computeFieldValue(item, fieldConfig.expression),
            fieldConfig.type
          )}
        </td>
      ))}
      <td className="actions-column">
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => navigate(`/edit/${item.id}`)}
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
          onClick={() => navigate('/new')}
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
                      {Object.entries(computedFields).map(([fieldId, fieldConfig]) => (
                        <th key={`computed-${fieldId}`}>{fieldConfig.label}</th>
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
    // Parse as local date to avoid timezone issues
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString();
  }

  return String(value);
}

function formatGroupName(groupName) {
  return groupName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatComputedValue(value, type) {
  if (value === null || value === undefined) {
    return '-';
  }

  if (type === 'date' && value) {
    // Parse as local date to avoid timezone issues
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString();
  }

  if (typeof value === 'number') {
    return Math.round(value);
  }

  return String(value);
}
