# Data Center Troubleshooting Lab

A small, isolated Linux and network diagnostics lab for practicing the investigation sequence used in infrastructure support: confirm the symptom, locate the failing layer, collect evidence, change one thing, and verify recovery.

**Status:** self-directed lab scaffold. Run the scenarios and record your own outputs before describing it as completed hands-on practice. This lab simulates a web service in containers; it is not a physical server, production data center, or proof of prior IT employment.

## Learning goals

- Diagnose name-resolution, TCP reachability, and HTTP response failures separately.
- Use Linux and Docker commands to inspect service state, logs, ports, and container networking.
- Capture a baseline, reproduce a fault, isolate a likely cause, apply a controlled recovery, and verify service.
- Write a concise incident timeline and handoff note.

## Requirements

- Docker Engine or Docker Desktop with the Docker Compose plugin.
- A terminal. No cloud account or external credentials are needed.

## Start the lab

From this directory:

```sh
docker compose up -d web
docker compose ps
```

Run the diagnostic client from inside the Compose network:

```sh
docker compose run --rm probe --host web --port 80 --path /health
```

A successful run reports DNS resolution, TCP connection, HTTP status, and elapsed time. From the host, the service is also available at `http://localhost:8080/health`.

Collect service evidence:

```sh
docker compose logs --timestamps web
docker compose exec web nginx -t
docker compose exec web sh -c 'ps; df -h'
```

## Incident scenarios

Run one scenario at a time. Save the terminal output in your incident log.

### 1. Name-resolution failure

```sh
docker compose run --rm probe --host web-missing --port 80 --path /health
```

Expected diagnostic layer: DNS/name resolution. Compare with the baseline host name `web`.

### 2. TCP port failure

```sh
docker compose run --rm probe --host web --port 81 --path /health
```

Expected diagnostic layer: TCP connection to the wrong/unlistened port. Check the service's configured listener and port mapping before changing anything.

### 3. HTTP application/path failure

```sh
docker compose run --rm probe --host web --port 80 --path /missing
```

Expected diagnostic layer: HTTP response. DNS and TCP should work; inspect the returned status and Nginx configuration.

### 4. Service unavailable

```sh
docker compose stop web
docker compose run --rm probe --host web --port 80 --path /health
docker compose start web
docker compose run --rm probe --host web --port 80 --path /health
```

Expected diagnostic layer: listener/service state. Compare before and after recovery, then inspect `docker compose ps` and timestamped logs.

## Investigation workflow

1. Write down the symptom, time, affected endpoint, and impact.
2. Check name resolution.
3. Check TCP reachability and the intended listening port.
4. Check the HTTP response and service logs.
5. Inspect service state and configuration.
6. Make one reversible change, then repeat the same diagnostic command.
7. Record the result, remaining uncertainty, and a safe handoff.

Use [evidence/incident-log-template.md](evidence/incident-log-template.md) for each scenario. Do not fill in example results as if they were observed; record your own run.

## Linux commands to practice

When working in a Linux VM or host, practice inspecting the operating system and network before restarting services:

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
curl -v http://127.0.0.1:8080/health
```

For this container lab, Docker's own service and network views are also useful:

```sh
docker compose ps
docker compose logs --timestamps web
docker network ls
docker network inspect data-center-troubleshooting-lab_default
```

## Project scope and honest description

The probe is a Python standard-library diagnostic utility; the service is Nginx in a local container. This gives repeatable practice with Linux-based service operations and DNS/TCP/HTTP fault isolation. It does not emulate server component replacement, RAID/storage failures, BMC/IPMI, switch configuration, or a production incident.

Once you have run the lab, you can describe the work accurately as a **self-directed containerized Linux and network troubleshooting lab**. Do not describe it as data-center employment or physical server repair.

## Repository layout

- `docker-compose.yml` - local service and probe containers
- `lab/nginx.conf` - health endpoint and static test service
- `lab/site/index.html` - service landing page
- `tools/diagnose.py` - DNS, TCP, and HTTP probe
- `evidence/incident-log-template.md` - evidence and handoff template
