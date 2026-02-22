import { isInMonth, monthDays } from "./date.js";

export function filterTransactionsByMonth(transactions, month) {
  return transactions.filter(tx => isInMonth(tx.date, month));
}

export function monthlyTotals(transactions, month) {
  const monthTx = filterTransactionsByMonth(transactions, month);
  const income = monthTx.filter(tx => tx.type === "income").reduce((sum, tx) => sum + tx.amount, 0);
  const expense = monthTx.filter(tx => tx.type === "expense").reduce((sum, tx) => sum + tx.amount, 0);
  return {
    income,
    expense,
    balance: income - expense
  };
}

export function categoryTotals(transactions, month, type = "expense") {
  const totals = new Map();
  for (const tx of transactions) {
    if (!isInMonth(tx.date, month) || tx.type !== type) {
      continue;
    }
    const key = tx.categoryId || tx.category;
    totals.set(key, (totals.get(key) || 0) + tx.amount);
  }
  return totals;
}

export function dailyBalanceSeries(transactions, month) {
  const days = monthDays(month);
  const series = [];
  let running = 0;
  const dailyTotals = new Map();

  for (const tx of transactions) {
    if (!isInMonth(tx.date, month)) {
      continue;
    }
    const delta = tx.type === "income" ? tx.amount : -tx.amount;
    dailyTotals.set(tx.date, (dailyTotals.get(tx.date) || 0) + delta);
  }

  for (const day of days) {
    running += dailyTotals.get(day) || 0;
    series.push({ date: day.slice(8), value: running });
  }

  return series;
}
