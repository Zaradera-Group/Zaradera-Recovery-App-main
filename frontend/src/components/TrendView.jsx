import CategoryBadge from "./CategoryBadge";

export default function TrendView({ trend, disappeared, onSelectLoan, comparisonDate }) {
  if (!comparisonDate) {
    return (
      <p className="empty-state">
        Trend needs at least two weekly uploads to compare. Come back after next week's sheet.
      </p>
    );
  }

  const worsening = trend.filter((t) => t.direction === "worsening").sort((a, b) => b.current_days_past_due - a.current_days_past_due);
  const improving = trend.filter((t) => t.direction === "improving");

  return (
    <div className="trend-view">
      <p className="trend-note">Compared with {comparisonDate}. Unchanged loans: {trend.filter((t) => t.direction === "unchanged").length}.</p>
      <section className="trend-section">
        <h3 className="trend-heading trend-heading-worsening">Worsening ({worsening.length})</h3>
        {worsening.length === 0 ? (
          <p className="empty-state">No loans worsened since the last upload.</p>
        ) : (
          <table className="loan-table">
            <thead>
              <tr>
                <th>Loan ID</th>
                <th>Borrower</th>
                <th>Product</th>
                <th className="num">Days (prev → now)</th>
                <th>Category (prev → now)</th>
              </tr>
            </thead>
            <tbody>
              {worsening.map((t) => (
                <tr key={t.loan_id} onClick={() => onSelectLoan(t.loan_id)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelectLoan(t.loan_id); } }}>
                  <td>{t.loan_id}</td>
                  <td>{t.borrower || "—"}</td>
                  <td>{t.loan_product || "—"}</td>
                  <td className="num">
                    {t.previous_days_past_due} → {t.current_days_past_due}
                  </td>
                  <td>
                    <CategoryBadge category={t.previous_category} /> → <CategoryBadge category={t.current_category} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="trend-section">
        <h3 className="trend-heading trend-heading-improving">Improving ({improving.length})</h3>
        {improving.length === 0 ? (
          <p className="empty-state">No loans improved since the last upload.</p>
        ) : (
          <table className="loan-table">
            <thead>
              <tr>
                <th>Loan ID</th>
                <th>Borrower</th>
                <th>Product</th>
                <th className="num">Days (prev → now)</th>
                <th>Category (prev → now)</th>
              </tr>
            </thead>
            <tbody>
              {improving.map((t) => (
                <tr key={t.loan_id} onClick={() => onSelectLoan(t.loan_id)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelectLoan(t.loan_id); } }}>
                  <td>{t.loan_id}</td>
                  <td>{t.borrower || "—"}</td>
                  <td>{t.loan_product || "—"}</td>
                  <td className="num">
                    {t.previous_days_past_due} → {t.current_days_past_due}
                  </td>
                  <td>
                    <CategoryBadge category={t.previous_category} /> → <CategoryBadge category={t.current_category} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {disappeared.length > 0 && (
        <section className="trend-section">
          <h3 className="trend-heading">No longer in the sheet ({disappeared.length})</h3>
          <p className="trend-note">
            These loan IDs were in the previous snapshot's upload but not the selected snapshot's — likely paid off or written off. Worth a quick check.
          </p>
          <ul className="disappeared-list">
            {disappeared.map((id) => (
              <li key={id}>
                <button className="link-button" onClick={() => onSelectLoan(id)}>
                  {id}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

