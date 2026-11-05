export function formatCount(count: number): string {
  if (!Number.isInteger(count) || count < 0) {
    throw new RangeError("Count must be a non-negative integer");
  }

  return `${count} ${count === 1 ? "click" : "clicks"}`;
}
