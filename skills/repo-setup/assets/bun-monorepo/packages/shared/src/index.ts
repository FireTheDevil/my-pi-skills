export function greeting(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) {
    throw new Error("Name must not be blank");
  }
  return `Hello, ${trimmed}!`;
}
