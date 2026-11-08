#!/usr/bin/env python3
"""Small standard-library probe for a local infrastructure troubleshooting lab."""
from __future__ import annotations

import argparse
import http.client
import socket
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DNS, TCP reachability, and HTTP response.")
    parser.add_argument("--host", default="localhost", help="Target hostname (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="Target TCP port (default: 8080)")
    parser.add_argument("--path", default="/health", help="HTTP request path (default: /health)")
    parser.add_argument("--timeout", type=float, default=3.0, help="Seconds per network operation")
    args = parser.parse_args()

    started = time.perf_counter()
    try:
        records = socket.getaddrinfo(args.host, args.port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        print(f"DNS_FAIL host={args.host} error={exc}")
        return 2

    addresses = sorted({item[4][0] for item in records})
    print(f"DNS_OK host={args.host} addresses={','.join(addresses)}")

    try:
        with socket.create_connection((args.host, args.port), timeout=args.timeout):
            pass
    except OSError as exc:
        print(f"TCP_FAIL target={args.host}:{args.port} error={exc}")
        return 3

    tcp_ms = (time.perf_counter() - started) * 1000
    print(f"TCP_OK target={args.host}:{args.port} elapsed_ms={tcp_ms:.1f}")

    try:
        connection = http.client.HTTPConnection(args.host, args.port, timeout=args.timeout)
        connection.request("GET", args.path, headers={"User-Agent": "dc-troubleshooting-lab/1.0"})
        response = connection.getresponse()
        body = response.read(160).decode("utf-8", errors="replace").replace("\n", " ").strip()
        status = response.status
        connection.close()
    except (OSError, http.client.HTTPException) as exc:
        print(f"HTTP_FAIL target={args.host}:{args.port}{args.path} error={exc}")
        return 4

    total_ms = (time.perf_counter() - started) * 1000
    print(f"HTTP_STATUS status={status} reason={response.reason}")
    if body:
        print(f"BODY_PREVIEW {body}")
    print(f"TOTAL elapsed_ms={total_ms:.1f}")

    if 200 <= status < 400:
        print("RESULT PASS")
        return 0
    print("RESULT HTTP_ERROR")
    return 4


if __name__ == "__main__":
    sys.exit(main())
