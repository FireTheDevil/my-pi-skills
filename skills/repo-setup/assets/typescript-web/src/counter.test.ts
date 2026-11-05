import { describe, expect, it } from "vitest";
import { formatCount } from "./counter";

describe("formatCount", () => {
  it("formats zero and plural counts", () => {
    expect(formatCount(0)).toBe("0 clicks");
    expect(formatCount(2)).toBe("2 clicks");
  });

  it("uses the singular for one click", () => {
    expect(formatCount(1)).toBe("1 click");
  });

  it("rejects negative and fractional counts", () => {
    expect(() => formatCount(-1)).toThrow(RangeError);
    expect(() => formatCount(1.5)).toThrow(RangeError);
  });
});
