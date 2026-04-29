import { makeOptions, request } from "./common.js";

export const options = makeOptions(10, "30s");

export default function () {
  request("/ping");
}
