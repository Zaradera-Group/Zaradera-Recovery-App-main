import { useState } from "react";
import LoanTable from "./LoanTable";

export default function GroupedView({ groups, onSelectLoan, groupOrder, sortKey, sortDirection, onSort }) {
  const keys = groupOrder ? groupOrder.filter((k) => groups[k]) : Object.keys(groups);
  const [collapsed, setCollapsed] = useState({});

  if (!keys.length) {
    return <p className="empty-state">No loans in this view.</p>;
  }

  return (
    <div className="grouped-view">
      {keys.map((key) => (
        <section key={key} className="loan-group">
          <button
            className="loan-group-header"
            onClick={() => setCollapsed((c) => ({ ...c, [key]: !c[key] }))}
            aria-expanded={!collapsed[key]}
          >
            <span>{key}</span>
            <span className="loan-group-count">{groups[key].length}</span>
          </button>
          {!collapsed[key] && (
            <LoanTable
              loans={groups[key]}
              onSelectLoan={onSelectLoan}
              sortKey={sortKey}
              sortDirection={sortDirection}
              onSort={onSort}
            />
          )}
        </section>
      ))}
    </div>
  );
}