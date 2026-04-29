import { makeOptions, request } from "./common.js";

export const options = makeOptions(500, "60s", {
  thresholds: {
    http_req_failed: ["rate<0.10"],
    checks: ["rate>0.90"],
  },
});

export default function () {
  const roll = Math.random();
  request(roll < 0.7 ? "/ping" : "/items");
}
