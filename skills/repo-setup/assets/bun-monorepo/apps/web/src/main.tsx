import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { greeting } from "@starter/shared";
import "./style.css";

function App() {
  const [count, setCount] = useState(0);
  return (
    <main>
      <h1>{greeting("Developer")}</h1>
      <button onClick={() => setCount((value) => value + 1)}>
        {count} clicks
      </button>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) throw new Error("Missing root element");
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
