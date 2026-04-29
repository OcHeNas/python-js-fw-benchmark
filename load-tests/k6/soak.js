import { makeOptions, request } from "./common.js";

export const options = makeOptions(100, "10m");

export default function () {
  const roll = Math.random();

  if (roll < 0.6) {
    request("/ping");
  } else if (roll < 0.9) {
    request("/items");
  } else {
    request("/io");
  }
}
