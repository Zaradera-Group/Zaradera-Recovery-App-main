function withinAmountRange(amount, min, max) {
  const value = amount || 0;
  if (min !== null && min !== undefined && value < min) return false;
  if (max !== null && max !== undefined && value > max) return false;
  return true;
}

export function filterFlatLoans(loans, min, max) {
  if (!loans) return loans;
  if (min === null && max === null) return loans;
  return loans.filter((loan) => withinAmountRange(loan.past_due_amount, min, max));
}

export function filterGroupedLoans(groups, min, max) {
  if (!groups) return groups;
  if (min === null && max === null) return groups;
  const result = {};
  for (const [key, loans] of Object.entries(groups)) {
    const filtered = loans.filter((loan) => withinAmountRange(loan.past_due_amount, min, max));
    if (filtered.length > 0) {
      result[key] = filtered;
    }
  }
  return result;
}