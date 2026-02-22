export function nowMonth() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export function todayDate() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export function isInMonth(dateString, month) {
  return dateString.startsWith(month);
}

export function formatCurrency(value) {
  return new Intl.NumberFormat("zh-Hant-TW", {
    style: "currency",
    currency: "TWD",
    maximumFractionDigits: 0
  }).format(value || 0);
}

export function monthDays(month) {
  const [year, mon] = month.split("-").map(Number);
  const date = new Date(year, mon - 1, 1);
  const days = [];
  while (date.getMonth() === mon - 1) {
    days.push(
      `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
    );
    date.setDate(date.getDate() + 1);
  }
  return days;
}
