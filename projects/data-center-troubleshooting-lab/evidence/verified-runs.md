# Verified local lab run

- Date: 2026-11-08
- Environment: Linux, Python 3.12.14
- Service: local Python HTTP server bound to 127.0.0.1:18080
- Docker Compose: not run; Docker was unavailable in this environment.
- Scope: local protocol/service diagnosis only; no physical server or network hardware.

## Baseline

```text
DNS_OK host=127.0.0.1 addresses=127.0.0.1
TCP_OK target=127.0.0.1:18080
HTTP_STATUS status=200 reason=OK
BODY_PREVIEW ok
RESULT PASS
```

## Reproduced faults

| Scenario | Observed result | Diagnostic layer |
|---|---|---|
| Reserved invalid hostname | DNS lookup failed; exit code 2 | Name resolution |
| Closed port 18081 | Connection refused; exit code 3 | TCP reachability/listener |
| GET /missing | HTTP 404; exit code 4 | HTTP path/application |
| GET /error | HTTP 503; exit code 4 | HTTP service response |
| Test service stopped | Connection refused; exit code 3 | Service availability |

## Recovery sequence

The service was started, checked at `/health`, stopped, and the same probe then detected a refused TCP connection. The baseline returned HTTP 200 while the service was running. The test service logged the successful health request and the two HTTP fault-path requests.

These are observed outputs from one local run. Timing is intentionally omitted because it varies between runs.
