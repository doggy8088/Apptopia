import test from "node:test";
import assert from "node:assert/strict";
import { csvToTransactions, transactionsToCsv } from "../src/lib/csv.js";

const sample = [
  {
    date: "2026-02-18",
    type: "expense",
    amount: 350,
    category: "餐飲",
    account: "現金",
    note: "午餐便當"
  },
  {
    date: "2026-02-19",
    type: "income",
    amount: 2000,
    category: "薪資",
    account: "銀行",
    note: ""
  }
];

test("transactionsToCsv outputs standard header and rows", () => {
  const csv = transactionsToCsv(sample);
  assert.ok(csv.startsWith("日期,類型,金額,分類,帳戶,備註"));
  assert.ok(csv.includes("2026-02-18,支出,350,餐飲,現金,午餐便當"));
});

test("csvToTransactions parses standard CSV format", () => {
  const csv = transactionsToCsv(sample);
  const parsed = csvToTransactions(csv);
  assert.equal(parsed.length, 2);
  assert.equal(parsed[0].type, "expense");
  assert.equal(parsed[1].type, "income");
  assert.equal(parsed[0].amount, 350);
});
