import CategoryBadge from "./CategoryBadge";
import { formatDate } from "../dateFormat";

function formatNaira(amount) {
  if (amount === null || amount === undefined) return "—";
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(amount);
}

function SortableHeader({ label, sortKey, activeKey, direction, onSort }) {
  const isActive = sortKey === activeKey;
  return (
    <th className="num">
      <button type="button" className="sort-header" onClick={() => onSort(sortKey)}>
        {label}
        <span className="sort-arrow">{isActive ? (direction === "asc" ? "▲" : "▼") : ""}</span>
      </button>
    </th>
  );
}

export default function LoanTable({ loans, onSelectLoan, sortKey, sortDirection, onSort }) {
  if (!loans.length) {
    return <p className="empty-state">No loans in this view.</p>;
  }

  return (
    <table className="loan-table">
      <thead>
        <tr>
          <th>Loan ID</th>
          <th>Borrower</th>
          <th>Product</th>
          <th>Approved</th>
          <SortableHeader
            label="Days past due"
            sortKey="days_past_due"
            activeKey={sortKey}
            direction={sortDirection}
            onSort={onSort}
          />
          <th>CBN category</th>
          <th>Tag</th>
          <SortableHeader
            label="Past due amount"
            sortKey="past_due_amount"
            activeKey={sortKey}
            direction={sortDirection}
            onSort={onSort}
          />
          <SortableHeader
            label="Portfolio at risk"
            sortKey="portfolio_at_risk"
            activeKey={sortKey}
            direction={sortDirection}
            onSort={onSort}
          />
        </tr>
      </thead>
      <tbody>
        {loans.map((loan) => (
          <tr key={loan.loan_id} onClick={() => onSelectLoan(loan.loan_id)} tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelectLoan(loan.loan_id);
              }
            }}>
            <td>{loan.loan_id}</td>
            <td>{loan.borrower || "—"}</td>
            <td>{loan.loan_product || "—"}</td>
            <td>{formatDate(loan.approved)}</td>
            <td className="num">{loan.days_past_due}</td>
            <td>
              <CategoryBadge category={loan.category} />
            </td>
            <td className="sheet-tag">{loan.sheet_classification || "—"}</td>
            <td className="num">{formatNaira(loan.past_due_amount)}</td>
            <td className="num">{formatNaira(loan.portfolio_at_risk)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
