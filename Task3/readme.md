# Задание 3. Масштабирование приложение под нагрузку

## Список файлов:

- deployment.yaml) - Deployment тестового приложения `ghcr.io/yandex-practicum/scaletestapp:latest` с одной стартовой репликой и лимитом памяти `30Mi`.
- service.yaml - Service для доступа к приложению и scrape-аннотациями Prometheus.
- hpa-memory.yaml - HPA по утилизации памяти, целевое значение `80%`, максимум `10` реплик.
- hpa-rps.yaml - HPA по RPS на pod через custom metric из Prometheus Adapter.
- [prometheus-adapter-values.yaml - values для установки Prometheus Adapter с правилом `http_requests_per_second`.
- locustfile.py - сценарий нагрузки для Locust.

## Проверочные логи:

- logs/hpa-memory-before.log - до нагрузки: `REPLICAS = 1`.
- logs/hpa-memory-scaled.log - HPA по памяти: событие `SuccessfulRescale`, размер изменился до `2`.
- logs/prometheus-metrics-after-fix.log - Prometheus target `up`, PromQL возвращает RPS, custom metric доступна через Kubernetes API.
- logs/hpa-rps-scaled.log - HPA по RPS: событие `SuccessfulRescale`, размер изменился до `5`.
- logs/hpa-rps-final-10-replicas.log - финальное состояние RPS-прогона: Deployment `10/10`, HPA дошел до максимума `10`.

```bash
kubectl -n scaletest set image deployment/scaletestapp \
  scaletestapp=ghcr.io/yandex-practicum/scaletestapp@sha256:7273dd1ffd1c1a29a307eb299b949f71828952b90dee42a5b26b052e92793452
```

## Проверка HPA по памяти

```bash
minikube start
minikube addons enable metrics-server

kubectl apply -f Task3/namespace.yaml
kubectl apply -f Task3/deployment.yaml
kubectl apply -f Task3/service.yaml
kubectl apply -f Task3/hpa-memory.yaml

kubectl -n scaletest rollout status deployment/scaletestapp
kubectl -n scaletest port-forward service/scaletestapp 8080:8080
```

В отдельном терминале:

```bash
cd Task3
locust --headless -u 300 -r 50 -t 3m --host http://localhost:8080
```

Проверка:

```bash
kubectl -n scaletest get hpa scaletestapp-memory --watch
kubectl -n scaletest get deployment scaletestapp
kubectl -n scaletest top pods
```

## Проверка HPA по RPS

Перед включением второго HPA нужно удалить HPA по памяти, чтобы два autoscaler не управляли одним Deployment одновременно:

```bash
kubectl -n scaletest delete hpa scaletestapp-memory
```

Установка Prometheus и Prometheus Adapter:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --set server.service.type=NodePort
helm upgrade --install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  -f Task3/prometheus-adapter-values.yaml
```

Проверка поступления метрик:

```bash
kubectl -n monitoring port-forward service/prometheus-server 9090:80
```

В Prometheus Web UI можно выполнить запрос:

```promql
sum(rate(http_requests_total{namespace="scaletest", pod!=""}[5m])) by (pod)
```

## Включение HPA по RPS:

```bash
kubectl apply -f Task3/hpa-rps.yaml
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/scaletest/pods/*/http_requests_per_second" | jq
kubectl -n scaletest get hpa scaletestapp-rps --watch
```

## Нагрузка:

```bash
cd Task3
locust --headless -u 300 -r 50 -t 3m --host http://localhost:8080
```

Целевое значение в [hpa-rps.yaml](hpa-rps.yaml) - `5` RPS на pod. Если локальный компьютер слабый, количество пользователей в Locust можно уменьшить или увеличить постепенно.

Если `kubectl port-forward` нестабилен во время перезапуска pod-ов, нагрузку можно сгенерировать внутри кластера:

```bash
kubectl -n scaletest run rps-load --rm -i --restart=Never \
  --image=curlimages/curl:8.17.0 -- sh -c \
  'until curl -sf http://scaletestapp:8080/ >/dev/null; do sleep 1; done;
   end=$(( $(date +%s) + 180 ));
   while [ $(date +%s) -lt $end ]; do curl -s http://scaletestapp:8080/ >/dev/null; done'
```
