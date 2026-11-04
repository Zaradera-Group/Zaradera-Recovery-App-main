const CATEGORY_KEY = {
  Performing: "performing",
  Watchlist: "watchlist",
  Substandard: "substandard",
  Doubtful: "doubtful",
  Lost: "lost",
};

// Shown as a native tooltip on hover — the CBN Deposit Money Bank day bands.
export const CATEGORY_DEFINITIONS = {
  Performing: "0–30 days past due — on track, no material risk.",
  Watchlist: "31–90 days past due — early warning, worth monitoring.",
  Substandard: "91–180 days past due — significant risk; typically provisioned against.",
  Doubtful: "181–360 days past due — full collection is doubtful under current conditions.",
  Lost: "361+ days past due — considered uncollectible through normal recovery efforts.",
};

export default function CategoryBadge({ category }) {
  const key = CATEGORY_KEY[category] || "watchlist";
  return (
    <span className={`badge badge-${key}`} title={CATEGORY_DEFINITIONS[category] || ""}>
      {category}
    </span>
  );
}