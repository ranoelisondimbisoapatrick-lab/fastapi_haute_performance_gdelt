import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  scenarios: {
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 10 },
        { duration: '40s', target: 30 },
        { duration: '20s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<1500'],
  },
};

export default function () {
  const q = encodeURIComponent('protest');
  const res = http.get(`http://localhost:8000/api/v1/events/search?query=${q}&limit=20`);
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(0.1);
}
