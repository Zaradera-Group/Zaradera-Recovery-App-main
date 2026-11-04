import { useEffect, useState } from "react";
import CategoryBadge from "./CategoryBadge";
import { getLoanHistory } from "../api";
import { formatDate } from "../dateFormat";

export default function LoanHistoryDrawer({ loanId, onClose }) {
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const previouslyFocused = document.activeElement;
    const closeButton = document.querySelector(".drawer-close");
    closeButton?.focus();
    function handleKey(event) {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        event.preventDefault();
        closeButton?.focus();
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
      previouslyFocused?.focus();
    };
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    setHistory(null);
    setError("");
    getLoanHistory(loanId)
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Could not load history.");
      });
    return () => {
      cancelled = true;
    };
  }, [loanId]);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" role="dialog" aria-modal="true" aria-labelledby="loan-history-title" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2 id="loan-history-title">Loan {loanId}</h2>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <p className="upload-message upload-message-error">{error}</p>}

        {!history && !error && <p className="empty-state">Loading history…</p>}

        {history && (
          <table className="loan-table">
            <thead>
              <tr>
                <th>Upload date</th>
                <th className="num">Days past due</th>
                <th>CBN category</th>
                <th>Tag</th>
                <th className="num">Past due amount</th>
              </tr>
            </thead>
            <tbody>
              {history.map((point) => (
                <tr key={point.upload_date}>
                  <td>{formatDate(point.upload_date)}</td>
                  <td className="num">{point.days_past_due}</td>
                  <td>
                    <CategoryBadge category={point.category} />
                  </td>
                  <td className="sheet-tag">{point.sheet_classification || "—"}</td>
                  <td className="num">
                    {point.past_due_amount != null
                      ? new Intl.NumberFormat("en-NG", {
                          style: "currency",
                          currency: "NGN",
                          maximumFractionDigits: 0,
                        }).format(point.past_due_amount)
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
