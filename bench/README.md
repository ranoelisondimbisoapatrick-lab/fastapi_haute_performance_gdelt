# Benchmarks (k6 + Locust)

## k6
Installe k6 puis :
```bash
k6 run bench/k6-smoke.js
k6 run bench/k6-search.js
```

## Locust
```bash
pip install locust
locust -f bench/locustfile.py --host http://localhost:8000
```
Ouvre ensuite l'UI locust : http://localhost:8089
