import { createServer } from "vite";

const server = await createServer({
  server: { host: "127.0.0.1", port: 0 },
});

try {
  await server.listen();
  const origin = server.resolvedUrls?.local[0];

  if (!origin) {
    throw new Error("Vite did not expose a local URL");
  }

  const page = await fetch(origin);
  const html = await page.text();

  if (!page.ok || !html.includes('id="counter"')) {
    throw new Error("Vite did not serve the starter page");
  }

  const moduleResponse = await fetch(new URL("src/main.ts", origin));

  if (!moduleResponse.ok) {
    throw new Error("Vite could not transform the application module");
  }

  console.log("PASS: Vite starts and serves the page and application module");
} finally {
  await server.close();
}
