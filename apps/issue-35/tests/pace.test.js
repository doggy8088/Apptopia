import assert from "node:assert/strict";
import test from "node:test";
import { formatPace, paceToSpeed, parsePaceInput, speedToPace } from "../src/lib/pace.js";

test("speed to pace conversion", () => {
  assert.equal(formatPace(speedToPace(10).totalSeconds), "6'00\"");
  assert.equal(formatPace(speedToPace(6).totalSeconds), "10'00\"");
  assert.equal(formatPace(speedToPace(15).totalSeconds), "4'00\"");
});

test("pace to speed conversion", () => {
  const pace = parsePaceInput("430");
  assert.equal(paceToSpeed(pace.totalSeconds), 13.3);
});

test("pace format normalization", () => {
  const pace = parsePaceInput("5:75");
  assert.equal(formatPace(pace.totalSeconds), "6'15\"");
});

test("invalid pace input", () => {
  assert.throws(() => parsePaceInput("abc"), /配速/);
});

test("format pace rejects invalid inputs", () => {
  assert.equal(formatPace(-1), null);
  assert.equal(formatPace(Number.NaN), null);
});
