from locust import HttpUser, constant, task


class LogisticsClient(HttpUser):
    wait_time = constant(0)

    @task(5)
    def failing_logistics(self):
        with self.client.get(
            "/logistics/error",
            name="/logistics/error -> fallback",
            catch_response=True,
        ) as response:
            if response.status_code == 200 and "fallback" in response.text:
                response.success()
            else:
                response.failure(
                    f"expected fallback, got {response.status_code}: {response.text[:120]}"
                )

    @task(1)
    def slow_logistics_timeout(self):
        with self.client.get(
            "/logistics/slow",
            name="/logistics/slow -> 3s timeout fallback",
            catch_response=True,
            timeout=6,
        ) as response:
            if response.status_code == 200 and "fallback" in response.text:
                response.success()
            else:
                response.failure(
                    f"expected timeout fallback, got {response.status_code}: {response.text[:120]}"
                )

    @task(1)
    def healthy_logistics(self):
        self.client.get("/logistics/fast", name="/logistics/fast")
