const W = 400;
const H = 180;
const PAD = { top: 12, right: 12, bottom: 36, left: 44 };
const CHART_W = W - PAD.left - PAD.right;
const CHART_H = H - PAD.top - PAD.bottom;

function toMs(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d).getTime();
}

function fmtDateShort(dateStr) {
  const [, m, d] = dateStr.split('-').map(Number);
  return `${m}/${d}`;
}

function fmtDateMed(dateStr) {
  const [y, m] = dateStr.split('-').map(Number);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${months[m - 1]} '${String(y).slice(2)}`;
}

function pickXTicks(sorted) {
  if (sorted.length === 1) return [sorted[0]];
  if (sorted.length === 2) return [sorted[0], sorted[sorted.length - 1]];
  return [
    sorted[0],
    sorted[Math.floor(sorted.length / 2)],
    sorted[sorted.length - 1],
  ];
}

export default function WeightChart({ items }) {
  if (items.length === 0) {
    return <div className="chart-empty">No data for this range.</div>;
  }

  const sorted = [...items].sort((a, b) => a.date.localeCompare(b.date));
  const weights = sorted.map(d => parseFloat(d.weight));
  const rawMin = Math.min(...weights);
  const rawMax = Math.max(...weights);
  const wRange = rawMax - rawMin;
  const yPad = Math.max(1, wRange * 0.15);
  const yMin = rawMin - yPad;
  const yMax = rawMax + yPad;
  const ySpan = yMax - yMin;

  const dates = sorted.map(d => toMs(d.date));
  const dMin = Math.min(...dates);
  const dMax = Math.max(...dates);
  const dSpan = dMax - dMin || 1;

  const cx = (dateStr) => PAD.left + ((toMs(dateStr) - dMin) / dSpan) * CHART_W;
  const cy = (w) => PAD.top + (1 - (parseFloat(w) - yMin) / ySpan) * CHART_H;

  const polyPoints = sorted.map(d => `${cx(d.date)},${cy(d.weight)}`).join(' ');

  // Y axis: 4 ticks
  const yTicks = Array.from({ length: 4 }, (_, i) => {
    const w = yMin + (ySpan / 3) * i;
    return { w, y: cy(w) };
  });

  // X axis: up to 3 ticks
  const xTicks = pickXTicks(sorted);
  const useLongFmt = dSpan > 90 * 24 * 60 * 60 * 1000;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="weight-chart-svg"
      preserveAspectRatio="xMidYMid meet"
      aria-label="Weight chart"
    >
      {/* Grid lines */}
      {yTicks.map(({ w, y }) => (
        <line key={w} x1={PAD.left} y1={y} x2={PAD.left + CHART_W} y2={y} stroke="#eee" strokeWidth="1" />
      ))}

      {/* Y axis */}
      <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + CHART_H} stroke="#ccc" strokeWidth="1" />
      {yTicks.map(({ w, y }) => (
        <g key={w}>
          <line x1={PAD.left - 4} y1={y} x2={PAD.left} y2={y} stroke="#ccc" strokeWidth="1" />
          <text x={PAD.left - 6} y={y} textAnchor="end" dominantBaseline="middle" fontSize="10" fill="#888">
            {Math.round(w * 10) / 10}
          </text>
        </g>
      ))}

      {/* X axis */}
      <line x1={PAD.left} y1={PAD.top + CHART_H} x2={PAD.left + CHART_W} y2={PAD.top + CHART_H} stroke="#ccc" strokeWidth="1" />
      {xTicks.map((item) => {
        const x = cx(item.date);
        const label = useLongFmt ? fmtDateMed(item.date) : fmtDateShort(item.date);
        return (
          <g key={item.date}>
            <line x1={x} y1={PAD.top + CHART_H} x2={x} y2={PAD.top + CHART_H + 4} stroke="#ccc" strokeWidth="1" />
            <text x={x} y={PAD.top + CHART_H + 14} textAnchor="middle" fontSize="10" fill="#888">{label}</text>
          </g>
        );
      })}

      {/* Data line */}
      {sorted.length > 1 && (
        <polyline points={polyPoints} fill="none" stroke="#3498db" strokeWidth="2" strokeLinejoin="round" />
      )}

      {/* Dots */}
      {sorted.map(d => (
        <circle
          key={d.id}
          cx={cx(d.date)}
          cy={cy(d.weight)}
          r="4"
          fill="#3498db"
          stroke="white"
          strokeWidth="1.5"
        />
      ))}
    </svg>
  );
}
