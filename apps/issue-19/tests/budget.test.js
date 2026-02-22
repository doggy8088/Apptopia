import test from "node:test";
import assert from "node:assert/strict";
import { monthlyTotals, categoryTotals, dailyBalanceSeries } from "../src/lib/budget.js";

const transactions = [
  { date: "2026-02-01", type: "income", amount: 3000, categoryId: "income-salary" },
  { date: "2026-02-03", type: "expense", amount: 200, categoryId: "expense-food" },
  { date: "2026-02-05", type: "expense", amount: 500, categoryId: "expense-food" },
  { date: "2026-02-05", type: "expense", amount: 100, categoryId: "expense-transport" }
];

test("monthlyTotals calculates income and expense", () => {
  const totals = monthlyTotals(transactions, "2026-02");
  assert.equal(totals.income, 3000);
  assert.equal(totals.expense, 800);
  assert.equal(totals.balance, 2200);
});

test("categoryTotals groups by category", () => {
  const totals = categoryTotals(transactions, "2026-02", "expense");
  assert.equal(totals.get("expense-food"), 700);
  assert.equal(totals.get("expense-transport"), 100);
});

test("dailyBalanceSeries builds running balance", () => {
  const series = dailyBalanceSeries(transactions, "2026-02");
  const day5 = series.find(item => item.date === "05");
  assert.equal(day5.value, 2200);
});
