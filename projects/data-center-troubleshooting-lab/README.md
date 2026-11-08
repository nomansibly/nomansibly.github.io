# Data Center Troubleshooting Lab

A small, isolated Linux and network diagnostics lab for practicing an infrastructure support workflow: confirm the symptom, locate the failing layer, collect evidence, change one thing, and verify recovery.

**Status:** self-directed training lab. It includes a local Python service and diagnostic probe, plus an optional Docker Compose/Nginx variant. This is not a physical server, production data center, or proof of prior IT employment.

## Learning goals

- Diagnose name-resolution, TCP reachability, and HTTP response failures separately.
- Inspect a Linux service, process, listening port, logs, and container network.
- Capture a baseline, reproduce a fault, isolate a likely cause, make a controlled recovery, and verify service.
- Write a concise incident timeline and handoff note.

## Quick start - no Docker required

Requirements: Python 3.10 or newer and a terminal.

In terminal 1, start the local test service:

```sh
python3 tools/serve.py --bind 127.0.0.1 --port 18080
```

In terminal 2, run the baseline check:

```sh
python3 tools/diagnose.py --host 127.0.0.1 --port 18080 --path /health
```

The probe reports DNS resolution, TCP connection, HTTP status, and elapsed time. The service exposes `/health` (200), `/error` (503), and a 404 for unknown paths. Use Ctrl+C in terminal 1 to stop it.

## Incident scenarios

Run one at a time and save your actual terminal outputs in the incident log.

### 1. Name-resolution failure

```sh
python3 tools/diagnose.py --host missing.data-center-lab.invalid --port 18080 --path /health
```

Expected layer: DNS/name resolution.

### 2. TCP port failure

```sh
python3 tools/diagnose.py --host 127.0.0.1 --port 18081 --path /health
```

Expected layer: TCP connection to an unlistened port.

### 3. HTTP path failure

```sh
python3 tools/diagnose.py --host 127.0.0.1 --port 18080 --path /missing
```

Expected layer: HTTP response. DNS and TCP should work; inspect the status and service logs.

### 4. Service error

```sh
python3 tools/diagnose.py --host 127.0.0.1 --port 18080 --path /error
```

Expected layer: HTTP 503 from the test service.

### 5. Service unavailable

Stop the service with Ctrl+C in terminal 1, then rerun the baseline command. It should report a TCP connection failure. Restart the service and repeat the baseline to verify recovery.

## Evidence from one local run

The checked-in [verified run log](evidence/verified-runs.md) records an actual local execution on Linux with Python 3.12.14. It includes a passing baseline and reproduced DNS, TCP, HTTP 404, HTTP 503, and service-down outcomes. The Docker Compose variant is included but was not run in that environment because Docker was unavailable.

## Optional Docker Compose/Nginx variant

If Docker Engine or Docker Desktop with Compose is installed, run from this directory:

```sh
docker compose up -d web
docker compose ps
docker compose run --rm probe --host web --port 80 --path /health
docker compose logs --timestamps web
docker compose exec web nginx -t
```

From the host, the Nginx service is at `http://localhost:8080/health`. The Compose probe runs inside the project network.

## Linux inspection commands

Practice inspecting state before restarting a service:

```sh
uname -a
uptime
ps aux
df -h
free -h
ip addr
ip route
ss -lntup
getent hosts example.local
curl -v http://127.0.0.1:18080/health
```

For the optional container version, also inspect:

```sh
docker compose ps
docker compose logs --timestamps web
docker network ls
```

## Investigation workflow

1. Record the symptom, time, affected endpoint, and impact.
2. Check name resolution.
3. Check TCP reachability and the intended listening port.
4. Check the HTTP response and service logs.
5. Inspect service state and configuration.
6. Make one reversible change, then repeat the same diagnostic command.
7. Record the result, remaining uncertainty, and a safe handoff.

Use [evidence/incident-log-template.md](evidence/incident-log-template.md) for each scenario. Do not fill in example results as if they were observed; record your own run.

## Honest scope

The native service and probe use Python's standard library on localhost. The optional variant runs Nginx in a container. This provides repeatable practice with DNS, TCP, HTTP, and basic Linux service diagnosis. It does not emulate physical server component replacement, RAID/storage failures, BMC/IPMI, switch configuration, or a production incident.

Accurately describe this as a **self-directed Linux and network troubleshooting lab**. Do not describe it as data-center employment or physical server repair.

## Repository layout

- `tools/diagnose.py` - DNS, TCP, and HTTP probe
- `tools/serve.py` - local HTTP service with health and fault endpoints
- `docker-compose.yml`, `lab/` - optional Nginx container variant
- `evidence/incident-log-template.md` - investigation and handoff template
- `evidence/verified-runs.md` - recorded local run outputs
