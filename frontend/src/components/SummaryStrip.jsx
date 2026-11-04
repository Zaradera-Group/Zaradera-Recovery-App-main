import { useState } from "react";
import CategoryBadge, { CATEGORY_DEFINITIONS } from "./CategoryBadge";
import CategoryPieChart from "./CategoryPieChart";
import { formatDate } from "../dateFormat";

const CATEGORY_ORDER = ["Performing", "Watchlist", "Substandard", "Doubtful", "Lost"];

function formatNaira(amount) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(amount || 0);
}

export default function SummaryStrip({ summary }) {
  const [showDefinitions, setShowDefinitions] = useState(false);

  if (!summary || !summary.latest_upload_date) {
    return (
      <div className="summary-strip summary-empty">
        No sheet uploaded yet — upload this week's file to get started.
      </div>
    );
  }

  return (
    <div className="summary-strip">
      <div className="summary-top">
        <div className="summary-headline">
          <span className="summary-date">Portfolio as of {formatDate(summary.latest_upload_date)}</span>
          <span className="summary-count">{summary.total_loans} past-due loans</span>
          <div className="summary-totals">
            <div>
              <span className="summary-total-label">Total past due</span>
              <span className="summary-total-value">{formatNaira(summary.total_past_due_amount)}</span>
            </div>
            <div>
              <span className="summary-total-label">Portfolio at risk</span>
              <span className="summary-total-value">{formatNaira(summary.total_portfolio_at_risk)}</span>
            </div>
          </div>
        </div>

        <CategoryPieChart counts={summary.by_category_counts} />

        <div className="summary-categories">
          {CATEGORY_ORDER.map((cat) => (
            <div key={cat} className="summary-category-pill">
              <CategoryBadge category={cat} />
              <span>{summary.by_category_counts[cat] || 0}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="definitions-toggle"
        onClick={() => setShowDefinitions((v) => !v)}
        aria-expanded={showDefinitions}
      >
        {showDefinitions ? "Hide" : "What do these categories mean?"}
      </button>

      {showDefinitions && (
        <dl className="definitions-list">
          {CATEGORY_ORDER.map((cat) => (
            <div key={cat} className="definitions-row">
              <dt>
                <CategoryBadge category={cat} />
              </dt>
              <dd>{CATEGORY_DEFINITIONS[cat]}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}