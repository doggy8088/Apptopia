import test from "node:test";
import assert from "node:assert/strict";
import { monthDays, normalizeDateInput } from "../src/lib/date.js";

test("normalizeDateInput pads and validates dates", () => {
  assert.equal(normalizeDateInput("2026-2-3"), "2026-02-03");
  assert.throws(() => normalizeDateInput("2026-02-30"), /日期不存在/);
});

test("monthDays builds full month list", () => {
  const days = monthDays("2026-02");
  assert.equal(days[0], "2026-02-01");
  assert.equal(days[days.length - 1], "2026-02-28");
  assert.equal(days.length, 28);
});
