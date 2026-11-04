export default function AmountFilter({ minAmount, maxAmount, onMinChange, onMaxChange }) {
  const hasFilter = minAmount !== "" || maxAmount !== "";

  return (
    <div className="amount-filter">
      <label htmlFor="amount-min">Past due amount</label>
      <input
        id="amount-min"
        type="number"
        min="0"
        placeholder="Min ₦"
        value={minAmount}
        onChange={(e) => onMinChange(e.target.value)}
      />
      <span className="amount-filter-sep">–</span>
      <input
        type="number"
        min="0"
        placeholder="Max ₦"
        value={maxAmount}
        onChange={(e) => onMaxChange(e.target.value)}
      />
      {hasFilter && (
        <button
          type="button"
          className="link-button"
          onClick={() => {
            onMinChange("");
            onMaxChange("");
          }}
        >
          Clear
        </button>
      )}
    </div>
  );
}