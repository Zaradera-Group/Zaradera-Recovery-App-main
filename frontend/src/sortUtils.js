function getSortValue(loan, key) {
  return loan[key] ?? 0;
}

export function sortLoans(loans, key, direction) {
  if (!loans || !key) return loans;
  return [...loans].sort((a, b) => {
    const diff = getSortValue(a, key) - getSortValue(b, key);
    return direction === "asc" ? diff : -diff;
  });
}

export function sortGroupedLoans(groups, key, direction) {
  if (!groups || !key) return groups;
  const result = {};
  for (const [groupKey, loans] of Object.entries(groups)) {
    result[groupKey] = sortLoans(loans, key, direction);
  }
  return result;
}