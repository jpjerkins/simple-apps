import { useState, useEffect, useRef } from 'react';
import WeightChart from './WeightChart';

const PAGE_SIZE = 10;

const RANGES = [
  { label: '1mo', days: 30 },
  { label: '3mo', days: 90 },
  { label: '1yr', days: 365 },
  { label: 'All', days: null },
];

function todayIso() {
  return new Date().toISOString().split('T')[0];
}

function filterByRange(items, days) {
  if (!days) return items;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const cutoffStr = cutoff.toISOString().split('T')[0];
  return items.filter(item => item.date >= cutoffStr);
}

function formatDate(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString();
}

export default function WeightView() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState('1mo');
  const [page, setPage] = useState(1);

  const [entryWeight, setEntryWeight] = useState('');
  const [entryDate, setEntryDate] = useState('');
  const [saving, setSaving] = useState(false);

  const [editItem, setEditItem] = useState(null);
  const [editWeight, setEditWeight] = useState('');
  const [editDate, setEditDate] = useState('');

  const weightInputRef = useRef(null);

  const loadItems = () => {
    fetch('/api/weight/items')
      .then(r => r.json())
      .then(data => {
        setItems(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => { loadItems(); }, []);

  const handleSave = (e) => {
    e.preventDefault();
    if (!entryWeight) return;
    setSaving(true);
    fetch('/api/weight/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        weight: parseFloat(entryWeight),
        date: entryDate || todayIso(),
      }),
    })
      .then(() => {
        setEntryWeight('');
        setEntryDate('');
        setPage(1);
        loadItems();
      })
      .finally(() => {
        setSaving(false);
        weightInputRef.current?.focus();
      });
  };

  const openEdit = (item) => {
    setEditItem(item);
    setEditWeight(String(item.weight));
    setEditDate(item.date);
  };

  const handleEditSave = () => {
    if (!editWeight || !editDate) return;
    fetch(`/api/weight/items/${editItem.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        weight: parseFloat(editWeight),
        date: editDate,
      }),
    }).then(() => {
      setEditItem(null);
      loadItems();
    });
  };

  const selectedRange = RANGES.find(r => r.label === range);
  const chartItems = filterByRange(items, selectedRange?.days ?? null);
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageItems = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="weight-view">
      {/* Chart */}
      <div className="weight-chart-container">
        {loading ? (
          <div className="chart-empty">Loading...</div>
        ) : (
          <WeightChart items={chartItems} />
        )}
      </div>

      {/* Range selector */}
      <div className="range-selector">
        {RANGES.map(r => (
          <button
            key={r.label}
            className={`range-btn${range === r.label ? ' range-btn-active' : ''}`}
            onClick={() => setRange(r.label)}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Easy entry form */}
      <form className="entry-form" onSubmit={handleSave}>
        <input
          ref={weightInputRef}
          className="entry-input entry-weight"
          type="number"
          inputMode="decimal"
          step="0.1"
          min="50"
          max="999"
          placeholder="lbs"
          value={entryWeight}
          onChange={e => setEntryWeight(e.target.value)}
        />
        <input
          className="entry-input entry-date"
          type="date"
          value={entryDate}
          onChange={e => setEntryDate(e.target.value)}
        />
        <button
          className="entry-save btn-primary"
          type="submit"
          disabled={saving || !entryWeight}
        >
          Save
        </button>
      </form>

      {/* Entries table */}
      {loading ? null : items.length === 0 ? (
        <div className="empty-state">No entries yet. Add your first weight above.</div>
      ) : (
        <div className="entries-section">
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Weight (lbs)</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map(item => (
                  <tr key={item.id}>
                    <td>{formatDate(item.date)}</td>
                    <td>{item.weight}</td>
                    <td className="actions-column">
                      <button
                        className="btn-sm btn-secondary"
                        onClick={() => openEdit(item)}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="btn-sm btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                ‹ Prev
              </button>
              <span className="page-info">Page {page} of {totalPages}</span>
              <button
                className="btn-sm btn-secondary"
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next ›
              </button>
            </div>
          )}
        </div>
      )}

      {/* Edit dialog */}
      {editItem && (
        <div className="dialog-overlay" onClick={() => setEditItem(null)}>
          <div className="dialog" onClick={e => e.stopPropagation()}>
            <h3 className="dialog-title">Edit Entry</h3>
            <div className="dialog-fields">
              <label className="dialog-label">
                Weight (lbs)
                <input
                  className="field-input"
                  type="number"
                  inputMode="decimal"
                  step="0.1"
                  min="50"
                  max="999"
                  value={editWeight}
                  onChange={e => setEditWeight(e.target.value)}
                  autoFocus
                />
              </label>
              <label className="dialog-label">
                Date
                <input
                  className="field-input"
                  type="date"
                  value={editDate}
                  onChange={e => setEditDate(e.target.value)}
                />
              </label>
            </div>
            <div className="dialog-actions">
              <button className="btn-primary" onClick={handleEditSave}>Save</button>
              <button className="btn-secondary" onClick={() => setEditItem(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
