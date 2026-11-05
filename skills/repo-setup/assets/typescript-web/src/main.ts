import "./style.css";
import { formatCount } from "./counter";

const counter = document.querySelector<HTMLButtonElement>("#counter");

if (!counter) {
  throw new Error("Missing counter button");
}

let count = 0;

counter.addEventListener("click", () => {
  count += 1;
  counter.textContent = formatCount(count);
});
