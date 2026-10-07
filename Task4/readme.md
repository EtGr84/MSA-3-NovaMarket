# Задание 4. Повысьте надёжность приложения

---

## Перечень файлов: 

- nginx-rate-limiter.conf - исправленная конфигурация Rate Limiter для web/mobile каналов.
  nginx-circuit-breaker.conf - конфигурация Circuit Breaker для прокси к логистическому сервису.
- rate_limiter.py - Locust-сценарий для проверки лимитов web/mobile.
- circuit_breaker.py- Locust-сценарий для проверки fallback-ответов Circuit Breaker.
- logs/circuit-breaker-headless.log - Locust получает fallback-ответы.
- logs/circuit-breaker-timeout.log - `/logistics/slow` завершается fallback примерно через `3s`, то есть проверяет timeout, а не только HTTP 5xx.
- logs/circuit-breaker-nginx-summary.log - NGINX показывает переход на fallback upstream после ошибок.
- logs/circuit-breaker-recovery.log - после `fail_timeout=30s` запрос снова идет в основной upstream.
- скриншоты


## Rate Limiter

Требования:

- web-приложение: до `50 r/s` с одного IP;
- mobile-приложение: до `30 r/s` с одного IP.

В NGINX сделаны две отдельные зоны лимитов. Ключ зоны выбирается через `map` по заголовку `Client-Type`: `web` попадает в `web_api`, `mobile` - в `mobile_api`. Пустой ключ не учитывается зоной, поэтому один location `/api/` может обслуживать оба канала с разными лимитами.

Локальная проверка через Docker:

```bash
docker run --rm --name novamarket-rate-limiter \
  -p 8080:8080 \
  -v "$PWD/Task4/nginx-rate-limiter.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine
```

В другом терминале:

```bash
locust -f Task4/rate_limiter.py --host=http://localhost:8080 --web-port=8082
```

Headless-вариант:

```bash
uvx locust -f Task4/rate_limiter.py --headless -u 200 -r 200 -t 20s \
  --host http://localhost:8080
```

Проверочный лог: [logs/rate-limiter-headless.log](logs/rate-limiter-headless.log). В нем есть ответы `429 Too Many Requests`, что подтверждает срабатывание rate limiter.

## Circuit Breaker

Требования:

- таймауты ответа и подключения: `3s`;
- после `5` неуспешных попыток upstream отключается на `30s`;
- в период отключения возвращается fallback-ответ;
- после `fail_timeout` NGINX снова пробует основной upstream.

В конфигурации основной upstream `127.0.0.1:9090` имеет `max_fails=5 fail_timeout=30s`. Backup upstream `127.0.0.1:9091` возвращает controlled fallback. В access log выводятся `upstream_addr` и `upstream_status`: после открытия circuit видно, что запросы идут напрямую на fallback upstream.

Для проверки именно таймаута endpoint `/slow` в тестовом logistics-сервисе не возвращает фиктивный мгновенный ответ. Он проксируется в TEST-NET blackhole upstream `192.0.2.1:81`, поэтому внешний `/logistics/` proxy ждет заголовки от основного upstream и срабатывает по `proxy_read_timeout 3s`, после чего отдает fallback. Query-вариант `?type=slow` переписывается на тот же `/slow`, чтобы в конфигурации не было декоративной "медленной" ветки с мгновенным `return 200`.

Локальная проверка через Docker:

```bash
docker run --rm --name novamarket-circuit-breaker \
  -p 8080:8080 \
  -v "$PWD/Task4/nginx-circuit-breaker.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine
```

В другом терминале:

```bash
locust -f Task4/circuit_breaker.py --host=http://localhost:8080 --web-port=8082
```

Headless-вариант:

```bash
uvx locust -f Task4/circuit_breaker.py --headless -u 20 -r 20 -t 20s \
  --host http://localhost:8080
```
