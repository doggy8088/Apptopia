import { describe, expect, it } from "vitest";
import { formatDuration, parseDurationToSeconds } from "../src/utils/duration";

describe("duration utils", () => {
  it("parses seconds", () => {
    expect(parseDurationToSeconds("45")).toBe(45);
  });

  it("parses minutes and seconds", () => {
    expect(parseDurationToSeconds("02:30")).toBe(150);
  });

  it("parses hours, minutes, seconds", () => {
    expect(parseDurationToSeconds("1:02:03")).toBe(3723);
  });

  it("formats duration", () => {
    expect(formatDuration(3723)).toBe("1:02:03");
    expect(formatDuration(150)).toBe("2:30");
  });
});
