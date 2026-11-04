// Formats an ISO date string ("2026-09-21") as "21.09.26" (dd.mm.yy).
// Underlying API values stay ISO (needed for query params and sorting) —
// this is purely a display-layer formatter.
export function formatDate(isoDate) {
  if (!isoDate) return "—";
  const [year, month, day] = isoDate.split("-");
  if (!year || !month || !day) return isoDate; // not an ISO date, show as-is
  return `${day}.${month}.${year.slice(-2)}`;
}