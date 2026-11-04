const COLORS = {
  Performing: "#2f8f5b",
  Watchlist: "#b3891f",
  Substandard: "#d97a2b",
  Doubtful: "#c24a2e",
  Lost: "#9e2a2a",
};

const CATEGORY_ORDER = ["Performing", "Watchlist", "Substandard", "Doubtful", "Lost"];

// Plain SVG donut chart — no charting library needed for 5 slices.
export default function CategoryPieChart({ counts }) {
  const entries = CATEGORY_ORDER.map((cat) => [cat, counts[cat] || 0]).filter(([, n]) => n > 0);
  const total = entries.reduce((sum, [, n]) => sum + n, 0);

  if (total === 0) {
    return null;
  }

  const radius = 60;
  const strokeWidth = 26;
  const circumference = 2 * Math.PI * radius;

  let offset = 0;
  const segments = entries.map(([cat, count]) => {
    const fraction = count / total;
    const dash = fraction * circumference;
    const segment = {
      cat,
      count,
      color: COLORS[cat],
      dasharray: `${dash} ${circumference - dash}`,
      dashoffset: -offset,
    };
    offset += dash;
    return segment;
  });

  return (
    <div className="pie-chart-wrap">
      <svg viewBox="0 0 160 160" width="120" height="120" className="pie-chart-svg">
        <g transform="rotate(-90 80 80)">
          {segments.map((seg) => (
            <circle
              key={seg.cat}
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeDasharray={seg.dasharray}
              strokeDashoffset={seg.dashoffset}
            />
          ))}
        </g>
        <text x="80" y="76" textAnchor="middle" className="pie-chart-total">
          {total}
        </text>
        <text x="80" y="94" textAnchor="middle" className="pie-chart-total-label">
          loans
        </text>
      </svg>
      <ul className="pie-chart-legend">
        {segments.map((seg) => (
          <li key={seg.cat}>
            <span className="pie-chart-swatch" style={{ background: seg.color }} />
            {seg.cat} ({seg.count})
          </li>
        ))}
      </ul>
    </div>
  );
}