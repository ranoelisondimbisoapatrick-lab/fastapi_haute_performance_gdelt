from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(1)
    def search(self):
        self.client.get("/api/v1/events/search", params={"query": "protest", "limit": 20})
