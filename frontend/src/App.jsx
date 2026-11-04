import { useCallback, useEffect, useState } from "react";
import UploadPanel from "./components/UploadPanel";
import SummaryStrip from "./components/SummaryStrip";
import LoanTable from "./components/LoanTable";
import GroupedView from "./components/GroupedView";
import TrendView from "./components/TrendView";
import LoanHistoryDrawer from "./components/LoanHistoryDrawer";
import AmountFilter from "./components/AmountFilter";
import {
  getSummary,
  getByProduct,
  getByDays,
  getByCategory,
  getTrend,
  getDisappeared,
  getUploadDates,
} from "./api";
import { formatDate } from "./dateFormat";
import { filterFlatLoans, filterGroupedLoans } from "./filterUtils";
import { sortLoans, sortGroupedLoans } from "./sortUtils";
import "./App.css";

const TABS = [
  { id: "days", label: "By days past due" },
  { id: "amount", label: "By amount" },
  { id: "product", label: "By product" },
  { id: "category", label: "By category" },
  { id: "trend", label: "Trend" },
];

const CATEGORY_ORDER = ["Performing", "Watchlist", "Substandard", "Doubtful", "Lost"];

export default function App() {
  const [activeTab, setActiveTab] = useState("days");
  const [uploadDates, setUploadDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(""); // "" = latest
  const [summary, setSummary] = useState(null);
  const [revision, setRevision] = useState(0);
  const [tabData, setTabData] = useState(null);
  const [trend, setTrend] = useState([]);
  const [disappeared, setDisappeared] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLoanId, setSelectedLoanId] = useState(null);
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [sortKey, setSortKey] = useState("days_past_due");
  const [sortDirection, setSortDirection] = useState("desc");

  const refreshAll = useCallback(async () => {
    setRevision((value) => value + 1);
  }, []);

   useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setTabData(null); // clear stale data from the previous tab immediately —
    // otherwise, for the brief moment before the new tab's fetch resolves,
    // activeTab already points at the new tab while tabData still holds the
    // old tab's shape (flat array vs grouped object), and the sort/filter
    // helpers below crash trying to treat one shape as the other.

    const dateParam = selectedDate || undefined;

    const load = async () => {
      try {
        const [summaryData, dates] = await Promise.all([getSummary(dateParam), getUploadDates()]);
        if (cancelled) return;
        setSummary(summaryData);
        setUploadDates(dates);
         if (activeTab === "days" || activeTab === "amount") {
          // Same flat list either way — "By amount" just defaults its sort
          // to past_due_amount instead of days_past_due (see handleTabClick).
          const data = await getByDays(dateParam);
          if (!cancelled) setTabData(data);
        } else if (activeTab === "product") {
          const data = await getByProduct(dateParam);
          if (!cancelled) setTabData(data);
        } else if (activeTab === "category") {
          const data = await getByCategory(dateParam);
          if (!cancelled) setTabData(data);
        } else if (activeTab === "trend") {
          const [trendData, disappearedData] = await Promise.all([getTrend(dateParam), getDisappeared(dateParam)]);
          if (!cancelled) {
            setTrend(trendData);
            setDisappeared(disappearedData);
          }
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Could not load this view.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [activeTab, selectedDate, revision]);

    function handleUploaded() {
    setSelectedDate("");
    refreshAll();
  }

   function handleTabClick(tabId) {
    setActiveTab(tabId);
    // Clear tabData here too, synchronously with activeTab — not just
    // inside the effect below. React batches these into the SAME render,
    // so there's no in-between render where activeTab says "product" but
    // tabData still holds the old tab's shape (that in-between render is
    // exactly what was crashing: the effect's own setTabData(null) runs
    // one render too late, after the mismatched render already threw).
    setTabData(null);
    if (tabId === "amount") {
      setSortKey("past_due_amount");
      setSortDirection("desc");
    } else if (tabId === "days") {
      setSortKey("days_past_due");
      setSortDirection("desc");
    }
  }

  function handleSort(key) {
    if (sortKey === key) {
      setSortDirection((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
  }

  const parsedMin = minAmount === "" ? null : Number(minAmount);
  const parsedMax = maxAmount === "" ? null : Number(maxAmount);

    const filteredFlatData =
    activeTab === "days" || activeTab === "amount"
      ? filterFlatLoans(tabData, parsedMin, parsedMax)
      : tabData;
  const filteredGroupedData =
    activeTab === "product" || activeTab === "category"
      ? filterGroupedLoans(tabData, parsedMin, parsedMax)
      : tabData;

  const sortedFlatData =
    activeTab === "days" || activeTab === "amount"
      ? sortLoans(filteredFlatData, sortKey, sortDirection)
      : filteredFlatData;
  const sortedGroupedData =
    activeTab === "product" || activeTab === "category"
      ? sortGroupedLoans(filteredGroupedData, sortKey, sortDirection)
      : filteredGroupedData;

  return (
    <div className="app">
      <div className="brand-bar">
        <span className="brand-mark">●</span> ZARADERA CREDIT
      </div>
      <header className="app-header">
        <div>
          <h1>Zaradera Recovery Unit</h1>
          <p className="app-subtitle">Past-due loan (PDL) segmentation and history</p>
        </div>
        <UploadPanel onUploaded={handleUploaded} />
      </header>

      {!loading && !error && <SummaryStrip summary={summary} />}

      <div className="filters-row">
        {uploadDates.length > 1 && (
          <div className="date-selector">
            <label htmlFor="upload-date">Viewing week</label>
            <select
              id="upload-date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            >
              <option value="">Latest ({formatDate(uploadDates[0])})</option>
              {uploadDates.slice(1).map((d) => (
                <option key={d} value={d}>
                  {formatDate(d)}
                </option>
              ))}
            </select>
          </div>
        )}

        {activeTab !== "trend" && (
          <AmountFilter
            minAmount={minAmount}
            maxAmount={maxAmount}
            onMinChange={setMinAmount}
            onMaxChange={setMaxAmount}
          />
        )}
      </div>

      <nav className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? "tab-active" : ""}`}
                        onClick={() => handleTabClick(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="tab-content">
        {error && <p className="upload-message upload-message-error">{error}</p>}
        {loading && !error && <p className="empty-state">Loading…</p>}

                {!loading && !error && (activeTab === "days" || activeTab === "amount") && sortedFlatData && (
          <LoanTable
            loans={sortedFlatData}
            onSelectLoan={setSelectedLoanId}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        )}

        {!loading && !error && activeTab === "product" && sortedGroupedData && (
          <GroupedView
            groups={sortedGroupedData}
            onSelectLoan={setSelectedLoanId}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        )}

        {!loading && !error && activeTab === "category" && sortedGroupedData && (
          <GroupedView
            groups={sortedGroupedData}
            onSelectLoan={setSelectedLoanId}
            groupOrder={CATEGORY_ORDER}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        )}

        {!loading && !error && activeTab === "trend" && (
          <TrendView trend={trend} disappeared={disappeared} onSelectLoan={setSelectedLoanId} comparisonDate={summary?.previous_upload_date} />
        )}
      </main>

      {selectedLoanId && (
        <LoanHistoryDrawer loanId={selectedLoanId} onClose={() => setSelectedLoanId(null)} />
      )}
    </div>
  );
}
