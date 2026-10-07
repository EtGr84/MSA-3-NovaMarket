from locust import HttpUser, constant, task


class WebClient(HttpUser):
    wait_time = constant(0)
    weight = 1

    @task
    def web_api(self):
        self.client.get(
            "/api/",
            headers={"Client-Type": "web"},
            name="/api/ [web]",
        )


class MobileClient(HttpUser):
    wait_time = constant(0)
    weight = 1

    @task
    def mobile_api(self):
        self.client.get(
            "/api/",
            headers={"Client-Type": "mobile"},
            name="/api/ [mobile]",
        )
