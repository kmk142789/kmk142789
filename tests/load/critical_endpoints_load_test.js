import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.LOAD_TEST_BASE_URL || 'http://localhost:8080';
const AUTH_TOKEN = __ENV.LOAD_TEST_AUTH_TOKEN || '';
const REQUEST_HEADERS = AUTH_TOKEN
  ? { headers: { Authorization: `Bearer ${AUTH_TOKEN}` } }
  : {};

export const options = {
  scenarios: {
    health: {
      executor: 'constant-arrival-rate',
      rate: 30,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 10,
      maxVUs: 30,
      exec: 'healthScenario',
    },
    ledger: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 15,
      maxVUs: 40,
      exec: 'ledgerScenario',
    },
    analytics: {
      executor: 'constant-arrival-rate',
      rate: 12,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 10,
      maxVUs: 30,
      exec: 'analyticsScenario',
    },
  },
  thresholds: {
    'http_req_duration{scenario:health}': ['p(95)<400'],
    'http_req_duration{scenario:ledger}': ['p(95)<550'],
    'http_req_duration{scenario:analytics}': ['p(95)<600'],
    'http_req_failed{scenario:health}': ['rate<0.01'],
    'http_req_failed{scenario:ledger}': ['rate<0.01'],
    'http_req_failed{scenario:analytics}': ['rate<0.015'],
    'http_reqs{scenario:health}': ['rate>25'],
    'http_reqs{scenario:ledger}': ['rate>18'],
    'http_reqs{scenario:analytics}': ['rate>10'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'max'],
};

function get(endpoint) {
  return http.get(`${BASE_URL}${endpoint}`, REQUEST_HEADERS);
}

export function healthScenario() {
  const res = get('/api/health');
  check(res, {
    'health status is 200': (r) => r.status === 200,
    'health body contains ok': (r) => r.body && r.body.toLowerCase().includes('ok'),
  });
  sleep(0.5);
}

export function ledgerScenario() {
  const res = get('/api/v1/ledger/summary');
  check(res, {
    'ledger summary is 200': (r) => r.status === 200,
    'ledger summary payload not empty': (r) => r.json('total', null) !== null,
  });
  sleep(0.5);
}

export function analyticsScenario() {
  const res = get('/api/v1/pulse/analytics');
  check(res, {
    'analytics response 200': (r) => r.status === 200,
    'analytics contains insights': (r) => Array.isArray(r.json('insights', [])),
  });
  sleep(1);
}

export function handleSummary(data) {
  return {
    'tests/load/results/critical-endpoints-summary.json': JSON.stringify(data, null, 2),
  };
}
