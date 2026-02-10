import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 10,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/health');
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(0.2);
}
