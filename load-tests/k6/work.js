import { makeOptions, request } from "./common.js";

export const options = makeOptions(100, "60s");

export default function () {
  const roll = Math.random();

  if (roll < 0.5) {
    request("/ping");
  } else if (roll < 0.8) {
    request("/items");
  } else {
    request("/io");
  }
}
