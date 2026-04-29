import http from "k6/http";
import { check, sleep } from "k6";

export function makeOptions(defaultVus, defaultDuration, extra = {}) {
  return {
    vus: Number(__ENV.VUS || defaultVus),
    duration: __ENV.DURATION || defaultDuration,
    summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
    thresholds: {
      http_req_failed: ["rate<0.05"],
      checks: ["rate>0.95"],
      ...(extra.thresholds || {}),
    },
  };
}

export function request(path) {
  const target = __ENV.TARGET || "http://localhost:8000";
  const response = http.get(`${target}${path}`, {
    tags: { endpoint: path },
  });

  check(response, {
    "status is 200": (r) => r.status === 200,
  });

  sleep(Number(__ENV.SLEEP_SECONDS || 0));
  return response;
}
