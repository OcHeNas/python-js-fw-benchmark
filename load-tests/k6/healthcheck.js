import http from "k6/http";
import { check } from "k6";

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: {
    checks: ["rate==1"],
  },
};

export default function () {
  const target = __ENV.TARGET || "http://localhost:8000";
  const response = http.get(`${target}/ping`);

  check(response, {
    "service is ready": (r) => r.status === 200,
  });
}
