import { makeOptions, request } from "./common.js";

export const options = makeOptions(100, "60s");

export default function () {
  request("/ping");
}
